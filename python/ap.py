import itertools
import numpy as np
import pandas as pd

import aux
import cfg
import db
import fio

# this module implements the two acoustic-prosodic entrainment measures we use
# note: in the result dataframes, an index of 0 for ses_id, tsk_id, or spk_id
#       indicates "all"; e.g., tsk_id 0 means "for all tasks in this session"



################################################################################
#                                AUX FUNCTIONS                                 #
################################################################################
# auxiliary functions used only internally within this module

def _normalize_features(df, nrm_type):
    ''' normalizes features in given dataframe in specified way 

    args:
        df: pandas dataframe with a "*_raw" column per feature
        nrm_type: how to normalize features (see cfg.NRM_TYPES)
    returns:
        input dataframe, with new columns with normalized features,
        "*_raw" columns removed
    '''
    assert nrm_type in cfg.NRM_TYPES, 'unknown normalization type'
    if nrm_type == cfg.NRM_RAW:
        print('no normalization requested, only renaming "_raw" columns')
        df.rename(columns={f + '_raw': f for f in cfg.FEATURES}, inplace=True)
    else:    
        # determine mean and standard deviation per speaker or gender
        grp_col = 'spk_id' if nrm_type == cfg.NRM_SPK else 'gender'
        df_raw = df.loc[:, [grp_col] + ['%s_raw' % f for f in cfg.FEATURES]]
        df_means = df_raw.groupby([grp_col]).mean()
        df_means.rename(
            columns={c:c[:-4] + '_mean' for c in df_means.columns}, 
            inplace=True)
        df = df.join(df_means, on=grp_col)
        df_stds = df_raw.groupby([grp_col]).std()
        df_stds.rename(
            columns={c:c[:-4] + '_std' for c in df_stds.columns}, inplace=True)
        df = df.join(df_stds, on=grp_col)
        # z-score normalize based on means and standard deviations
        for f in cfg.FEATURES:
            df_zf = (df[f + '_raw'] - df[f + '_mean']) / df[f + '_std']
            df_zf.name = f
            df = df.join(df_zf)
    # remove columns with raw features and feature stats
    cols = [[f + '_raw', f + '_mean', f + '_std'] for f in cfg.FEATURES_ALL]
    cols = list(itertools.chain(*cols))
    df.drop(cols, axis=1, inplace=True, errors='ignore')
    return df


def _join_task_data(df):
    ''' loads task meta-data and joins them to given dataframe

    args:
        df: pandas dataframe with a "tsk_id" column
    returns:
        input dataframe with new, added task meta-data columns
    '''
    df_tsk = db.pd_read_sql_query('SELECT * FROM tasks')
    df_tsk.drop(['ses_id', 'task_index', 'a_or_b'], axis=1, inplace=True)
    df_tsk.set_index('tsk_id', inplace=True)
    return df.join(df_tsk, on='tsk_id')


def _compute_sims(df):
    ''' computes similarity betw. paired chunks/tasks/sessions for all features 

    args:
        df: pandas dataframe with pairs of feature values, either individual 
            values (for chunk pairs) or means (for speakers in tasks/sessions) 
    returns:
        input dataframe with new, added "*_sim" columns, one per feature
    '''
    for f in cfg.FEATURES:
        sims_f = -abs(df[f] - df[f + '_paired'])
        sims_f.name = f + '_sim'
        df = df.join(sims_f)
    return df


def _load_pairs(df, extra_cols=[]):
    ''' loads chunk pairs and joins with given data, features, and extra columns

    args:
        df: pandas dataframe with normalized features per chunk
        extra_paired_cols: extra columns, in addition to features, to include 
            regarding paired chunks
    returns:
        pandas dataframe with chunk pairs (with features) per row 
    '''
    # tmp1: pairs of chunk ids (adjacent and non-adjacent turn exchange chunks)
    tmp1 = db.pd_read_sql_query(
        'SELECT p_or_x, chu_id1, chu_id2, rid FROM chunk_pairs')
    # tmp2: all chu_ids with respective feature values and extra columns
    loc_cols = ['chu_id'] + cfg.FEATURES + extra_cols
    tmp2 = df.loc[:, loc_cols].set_index('chu_id')
    # tmp3: df joined with pairs -> df with second, turn-final, paired chu_id
    tmp3 = df.join(tmp1.set_index('chu_id2'), on='chu_id')
    # final step: full df data joined with features of paired, turn-final chu_id
    df = tmp3.join(tmp2, rsuffix='_paired', on='chu_id1')
    df.rename(columns={'chu_id1': 'chu_id_paired'}, inplace=True)
    # reset to running index
    df.reset_index(drop=True, inplace=True)
    # add columns for similarity between paired chunks for all features
    df = _compute_sims(df)
    return df



################################################################################
#                                MAIN FUNCTIONS                                #
################################################################################

def load_data(nrm_type, extra_paired_cols=[]):
    ''' loads data into one wide dataframe with redundant info 
    
    args: 
        nrm_type: how to normalize features (see cfg.NRM_TYPES)
        extra_paired_cols: extra columns to include regarding paired speakers
    returns:
        pandas dataframe with data per chunk (or chunk pair, where applicable),
        with running index (not chu_id because non-adjacent chunk pairs lead to 
        multiple rows per chunk)
    '''
    # load raw data ("big table" dataframe with redundant info)
    df_bt = db.pd_read_sql_query(sql_fname=cfg.SQL_BT_FNAME)
    # normalize features as needed
    df_bt = _normalize_features(df_bt, nrm_type)
    # join task meta-data (these differ by corpus, not loaded in script above)
    df_bt = _join_task_data(df_bt)
    # add features of paired chunks (partner and non-partner) to each row and
    # compute similarity for each pair and all features
    df_bt = _load_pairs(df_bt, extra_paired_cols)
    return df_bt


def syn(df_bt):
    ''' computes synchrony for given data, per session, task, and speaker

    args:
        df_bt: "big table" pandas dataframe as returned by load_data
        grp_by: list of constants from cfg.GRP_BYS, for which groups of data
            the measure should be computed
    returns:
        pandas dataframe with results (r-value, p-value, degrees of freedom), 
        indexed by ses_id, tsk_id, and spk_id
        (0 for any index component means "all", e.g., all tasks in a session)
    '''
    def __syn_test(df, f):
        ''' runs sanity checks and the actual pearsonr for synchrony '''
        # exclude lists that are too short or constant (pearsonr undefined)
        if len(df) < 3 or np.std(df[f]) == 0:
            return (np.nan, np.nan, len(df)-2)
        else:
            # compute correlation between turn-final and turn-initial chunks
            return aux.pearsonr(df[f], df[f + '_paired'])
    # compute synchrony for each feature per task and speaker
    results = {f: {} for f in cfg.FEATURES}
    for ses_id, df_grp_ses in df_bt[df_bt['p_or_x'] == 'p'].groupby('ses_id'):
        for f in cfg.FEATURES:
            # exclude nan (NULL) feature values
            df_grp_ses_f = df_grp_ses[pd.notna(df_grp_ses[f])]
            df_grp_ses_f = df_grp_ses_f[pd.notna(df_grp_ses_f[f + '_paired'])]
            for tsk_id, df_grp_ses_tsk in df_grp_ses_f.groupby('tsk_id'):
                for spk_id, df_grp_ses_tsk_spk \
                in df_grp_ses_tsk.groupby('spk_id'):
                    # result per task, asymmetric measure per speaker
                    results[f][(ses_id, tsk_id, spk_id)] = \
                        __syn_test(df_grp_ses_tsk_spk, f)
    return aux.get_df(results, ['ses_id', 'tsk_id', 'spk_id'])


def lcon(df_bt):
    ''' computes local convergence for given data, per session and speaker

    args:
        df_bt: "big table" pandas dataframe as returned by load_data
        grp_by: list of constants from cfg.GRP_BYS, for which groups of data
            the measure should be computed
    returns:
        pandas dataframe with results (r-value, p-value, degrees of freedom), 
        indexed by ses_id, and spk_id
        (0 for spk_id index means both speakers in that session)
    '''
    def __lcon_test(df, f):
        if len(df) < 3 or np.std(df[f + '_sim']) == 0:
            # exclude lists that are too short or constant (pearsonr undefined)
            return (np.nan, np.nan, len(df)-2)
        else:
            # compute correlation between similarity and turn-initial start time
            return aux.pearsonr(df[f + '_sim'], df['start_time'])
    # note: correlating with turn_index_ses makes very little difference
    results = {f: {} for f in cfg.FEATURES}
    for ses_id, df_grp_ses in df_bt[df_bt['p_or_x'] == 'p'].groupby('ses_id'):
        for f in cfg.FEATURES:
            # exclude nan (NULL) feature values
            df_grp_ses_f = df_grp_ses[pd.notna(df_grp_ses[f + '_sim'])]
            for tsk_id, df_grp_ses_tsk in df_grp_ses_f.groupby('tsk_id'):
                for spk_id, df_grp_ses_tsk_spk \
                in df_grp_ses_tsk.groupby('spk_id'):
                    # result per task, asymmetric measure per speaker
                    results[f][(ses_id, tsk_id, spk_id)] = \
                        __lcon_test(df_grp_ses_tsk_spk, f)
    # note: normally, we do not compute convergence per task as it is not 
    #       meaningful for short tasks; but in fisher, tasks and sessions are 
    #       the same so it does not matter and in xcdc there are only two tasks
    #       representing relatively long interviews
    return aux.get_df(results, ['ses_id', 'tsk_id', 'spk_id'])






