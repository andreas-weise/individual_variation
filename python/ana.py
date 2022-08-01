import itertools
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats

import aux
import cfg

# this module implements functions for the analysis of entrainment results



identity = lambda x:x

def _get_data(series, stat_idx, func=identity):
    ''' extracts data from tuples and applies func if needed '''
    data = series
    if stat_idx is not None:
        data = list(map(func, list(zip(*data))[stat_idx]))
    return data


def _compare_binary(df, col, lvl0, lvl1):
    ''' runs t-tests for number, length, and speed of ipus for levels of col

    used to compare speakers based on gender and native language '''
    def _run_test(x, y, title, col, lvl0, lvl1):
        ''' prints statistics of given series and runs the actual t-test '''
        print('%s (%s == %s): %.2f (%.2f)' % 
              (title, col, lvl0, x.mean(), x.std()))
        print('%s (%s == %s): %.2f (%.2f)' % 
              (title, col, lvl1, y.mean(), y.std()))
        print(aux.ttest_ind(x, y))
    # split the data by the given two levels of the relevant column
    df0 = df[df[col] == lvl0]
    df1 = df[df[col] == lvl1]
    # number of unique turn-final and turn-initial ipus per speaker
    x = df0.groupby('spk_id').count()['cnt']
    y = df1.groupby('spk_id').count()['cnt']
    _run_test(x, y, 'number of relevant IPUs per speaker', col, lvl0, lvl1)
    # mean speech rate per speaker
    x = df0.groupby('spk_id')['rate_syl'].mean()
    y = df1.groupby('spk_id')['rate_syl'].mean()
    _run_test(x, y, 'speech rate of relevant IPUs per speaker', col, lvl0, lvl1)
    # mean ipu duration per speaker
    x = df0.groupby('spk_id')['duration'].mean()
    y = df1.groupby('spk_id')['duration'].mean()
    _run_test(x, y, 'duration of relevant IPUs per speaker', col, lvl0, lvl1)
    # mean number of syllables per ipu per speaker; number of syllables can be 
    # recovered from speech rate and duration if speech rate is unnormalized
    get_syl_cnt = lambda x: x['rate_syl'] * x['duration']
    x = df0.groupby('spk_id').apply(get_syl_cnt).groupby('spk_id').mean()
    y = df1.groupby('spk_id').apply(get_syl_cnt).groupby('spk_id').mean()
    _run_test(x, y, 'syllables per relevant IPU per speaker', col, lvl0, lvl1)
    print('\n')


def annotate_local_measure(df):
    ''' add columns to df summarizing significant results across features

    args:
        df: pandas dataframe with at least two values per cell, representing a
            test statistic (index 0) and a p-value (index 1)
            (same format as returned by lsim, lcon, syn functions in ap)
    returns:
        input dataframe with four new columns
    '''
    func = lambda x: len(
        [1 for f in cfg.FEATURES if x[f][1] <= 0.05 and x[f][0] > 0])
    df['+'] = df.apply(func, axis=1)
    func = lambda x: len(
        [1 for f in cfg.FEATURES if x[f][1] <= 0.05 and x[f][0] < 0])
    df['-'] = df.apply(func, axis=1)
    func = lambda x: x['+'] + x['-']
    df['+/-'] = df.apply(func, axis=1)
    func = lambda x: \
        '0' if x['+'] == 0 and x['-'] == 0 \
        else '+' if x['+'] > 0 and x['-'] == 0 \
        else '-' if x['+'] == 0 and x['-'] > 0 \
        else '+/-'
    df['pm_type'] = df.apply(func, axis=1)
    return df


def add_speaker_info(df, df_bt):
    ''' adds speaker meta data to df with entrainment measure results
    
    args:
        df: pandas dataframe as returned by entrainment measure functions
        df_bt: "big table" pandas dataframe as returned by ap.load_data
    returns:
        df with additional columns for speaker/partner gender/language 
        plus speaker identifier (A/B), role, and years of english experience
    '''
    loc_cols = [
        'gender', 'native_lang', 'gender_paired', 'native_lang_paired', 
        'speaker_a_or_b', 'speaker_role', 'eng_yrs'
    ]
    return df.join(
        df_bt.groupby(['ses_id', 'tsk_id', 'spk_id']).first().loc[:, loc_cols])


def filter_half_of_matches(corpus_id, df):
    ''' filters out half of rows with matching speaker/partner gender&language

    for fisher, removes speaker "B" for those rows; for xcdc, removes selection

    args:
        corpus_id: one of the constants defined in cfg, identifying the corpus
        df: pandas dataframe including speaker type and a/b columns (for fc)
            or index columns 
    returns:
        input dataframe with some rows filtered out
    '''
    cfg.check_corpus_id(corpus_id)
    if corpus_id == cfg.CORPUS_ID_FC:
        f1 = df['gender']==df['gender_paired']
        f2 = df['native_lang']==df['native_lang_paired']
        f3 = df['speaker_a_or_b']=='B'
        df_res = df[~(f1&f2&f3)]
    else: # corpus_id == cfg.CORPUS_ID_DC
        # remove specific selection of tasks & speakers
        df_res = df.reset_index()
        func = lambda x: (x['tsk_id'], x['spk_id']) not in cfg.TSK_SPK_EXCL_DC
        df_res['include'] = df_res.apply(func, axis=1)
        df_res = df_res[df_res['include']]
        df_res.set_index(['ses_id', 'tsk_id', 'spk_id'], inplace=True)
        df_res.drop(['include'], axis=1, inplace=True)
    return df_res


def get_stats(df, title):
    ''' print entraining speaker stats based on given measure dataframe '''
    print(title)
    df1 = df.groupby(['pm_type']).count()[['+']].reset_index().rename(
        columns={'pm_type': 'id', '+': 'cnt'})
    func1 = lambda x: round(x['cnt'] / sum(df1['cnt']), 3)
    df1['pct_ttl'] = df1.apply(func1, axis=1)
    get_pct = lambda x: round(100 * x, 1)
    print('Entraining speakers: %.1f%%' % 
          get_pct(1 - df1[df1['id']=='0']['pct_ttl']))
    
    func2 = lambda x: round(x['cnt'] / sum(df1[df1['id']!='0']['cnt']), 3)
    df1['pct_ent'] = df1.apply(func2, axis=1)
    print('Valence')
    print('\tpositive: %.1f' % get_pct(df1[df1['id']=='+']['pct_ent']))
    print('\tnegative: %.1f' % get_pct(df1[df1['id']=='-']['pct_ent']))
    print('\tmixed:    %.1f' % get_pct(df1[df1['id']=='+/-']['pct_ent']))
    
    df2 = df.groupby(['+/-']).count()[['+']].reset_index().rename(
        columns={'+/-': 'id', '+': 'cnt'}).astype({'id': str})
    df2['pct_ent'] = df2.apply(func2, axis=1)
    print('#Features')
    print('\t1:   %.1f' % get_pct(df2[df2['id']=='1']['pct_ent']))
    print('\t2:   %.1f' % get_pct(df2[df2['id']=='2']['pct_ent']))
    print('\t3+:  %.1f' % get_pct(sum(df2['pct_ent'].iloc[3:])))
    print('\tmax: %d' % max(df['+/-']))


def get_chart(corpus_id, df, title):
    ''' produce stacked bar chart of valence percentages per speaker group '''
    # 'x' is for missing speaker types in fisher
    df_all = pd.DataFrame(index=['+', '-', '+/-', '0', 'x'])
    grp_cols = ['gender', 'native_lang', 'gender_paired', 'native_lang_paired']
    for (g, nl, g_p, nl_p), df_grp in df.groupby(grp_cols):
        speaker_type = g.upper() + nl[0] + '-' + g_p.upper() + nl_p[0]
        df_grp = df_grp.groupby(['pm_type']).count()[['+']]
        func = lambda x, total: round(x['+'] / total, 3)
        df_grp[speaker_type] = df_grp.apply(func, axis=1, total=sum(df_grp['+']))
        df_grp = df_grp.reindex(['+', '-', '+/-', '0', 'x'], fill_value=0)
        df_grp.drop(['+'], axis=1, inplace=True)
        df_all = df_all.join(df_grp)
        if corpus_id == cfg.CORPUS_ID_FC:
            df_all['FC-FC'] = [0.0, 0.0, 0.0, 0.0, 1.0]
            df_all['FC-MC'] = [0.0, 0.0, 0.0, 0.0, 1.0]
            df_all['MC-FC'] = [0.0, 0.0, 0.0, 0.0, 1.0]
            df_all['MC-MC'] = [0.0, 0.0, 0.0, 0.0, 1.0]
        df_all = df_all[sorted(df_all.columns)]

    pcts_m = df_all.iloc[1,:]
    pcts_p = df_all.iloc[0,:]
    pcts_pm = df_all.iloc[2,:]
    pcts_0 = df_all.iloc[3,:]
    pcts_x = df_all.iloc[4,:]
    pcts_pm_sum = [pcts_m[i] + pcts_p[i] for i in range(len(pcts_m))]
    pcts_pmpm_sum = [pcts_p[i] + pcts_m[i] + pcts_pm[i] 
                     for i in range(len(pcts_p))]

    x = range(len(pcts_m))
    fig, ax = plt.subplots()
    fig.set_size_inches(18, 9)
    plt.tick_params(axis='both', which='major', 
                    labelsize=30, width=3, length=7)
    plt.title(title, fontsize=35)

    p_m = ax.bar(x, pcts_m, color='#EEEEEE', hatch='-', label='-')
    p_p = ax.bar(x, pcts_p, bottom=pcts_m, color='#BBBBBB', 
                 hatch='+', label='+')
    p_pm = ax.bar(x, pcts_pm, bottom=pcts_pm_sum, color='#999999', 
                  hatch='xx', label='+/-')
    p_0 = ax.bar(x, pcts_0, bottom=pcts_pmpm_sum, color='#666666', 
                 hatch='', label='0')
    p_x = ax.bar(x, pcts_x, color='#FFFFFF', label='x')

    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.1,
                     box.width, box.height * 0.9])
    ax.legend()
    plt.xticks(x, df_all.columns, rotation=90)
    plt.yticks(np.arange(0, 1.01, 0.1))
    ax.legend((p_0[0], p_pm[0], p_p[0], p_m[0]), ('0', '+/-', '+', '-'),
               prop={'size': 25}, loc='upper center', 
               bbox_to_anchor=(0.5, -0.242),
               fancybox=True, shadow=True, ncol=4)
    plt.show()


def prep_for_anova(df_in, func=aux.r2z):
    ''' convert dataframe to right format for anova analysis '''
    df_out = pd.DataFrame()
    get_label = lambda x, col: x[col][0].upper()
    df_out['g'] = df_in.apply(get_label, axis=1, args=['gender']) \
                + df_in.apply(get_label, axis=1, args=['gender_paired'])
    df_out['l'] = df_in.apply(get_label, axis=1, args=['native_lang']) \
                + df_in.apply(get_label, axis=1, args=['native_lang_paired'])
    for f in cfg.FEATURES:
        df_out[f] = _get_data(df_in[f], 0, func)
    return df_out


def correlate_eng_yrs(df, title, func=aux.r2z):
    ''' correlates given measure with speakers' years of english experience '''
    df = df[df['native_lang'] == 'Chinese']
    df = df[pd.notna(df['eng_yrs'])]
    print(title)
    for f in cfg.FEATURES:
        print(f, aux.pearsonr(_get_data(df[f], 0, func), df['eng_yrs']))
    print()


def compare_spk_in_both_roles(df_ee, df_er, title):
    ''' compares each speaker with themselves as interviewee/er '''
    # sort to ensure same speakers in same rows across dataframes
    df_ee = df_ee.sort_values(by=['ses_id', 'spk_id'], axis=0)
    df_er = df_er.sort_values(by=['ses_id', 'spk_id'], axis=0)
    print(title)
    for f in cfg.FEATURES:
        x = _get_data(df_ee[f], 0, aux.r2z)
        y = _get_data(df_er[f], 0, aux.r2z)
        t, p, dof = aux.ttest_rel(x, y)
        d = aux.cohen_d(x, y)
        print(f, round(t, 6), p, dof, round(d, 6))
    print()


def compare_valence_per_spk_type(df, title):
    ''' compares #speakers with only pos/neg valence across spk types '''
    df = df.copy()
    # only consider those with entirely positive or negative valence
    df = df[(df['pm_type']=='+')|(df['pm_type']=='-')]
    # compute count per speaker type and valence
    df['cnt'] = 1
    grp_cols = ['gender', 'native_lang', 
                'gender_paired', 'native_lang_paired',
                'pm_type']
    df = df.groupby(grp_cols).count()[['cnt']]
    # self-join to get results for both valences in same row and run test
    df = df.xs('+', level=4).join(df.xs('-', level=4), 
        lsuffix='_+', 
        rsuffix='_-',
        how='outer'
    ).fillna(0)
    print(title, aux.ttest_rel(df['cnt_+'], df['cnt_-']))


def compare_sig_cnt_within_corpus(df_lcon, df_syn, title):
    ''' compares #sig. speakers across measures within corpus '''
    obs = [[len(df_lcon[df_lcon['pm_type']!='0']),
            len(df_lcon[df_lcon['pm_type']=='0'])], 
           [len(df_syn[df_syn['pm_type']!='0']),
            len(df_syn[df_syn['pm_type']=='0'])]]
    chi2, p, dof, exp = scipy.stats.contingency.chi2_contingency(obs)
    print(title, chi2, p, dof)


def compare_sig_cnt_across_corpora(df_ee, df_er, df_fc, title):
    ''' compares #sig. speakers within measure across corpora '''
    obs = [[len(df_ee[df_ee['pm_type']!='0']),
            len(df_ee[df_ee['pm_type']=='0'])], 
           [len(df_er[df_er['pm_type']!='0']),
            len(df_er[df_er['pm_type']=='0'])], 
           [len(df_fc[df_fc['pm_type']!='0']),
            len(df_fc[df_fc['pm_type']=='0'])]]
    chi2, p, dof, exp = scipy.stats.contingency.chi2_contingency(obs)
    print(title, chi2, p, dof)


def compare_sig_fea_cnt_across_corpora(df_ee, df_er, df_fc, title):
    ''' compares #speakers per sig. feature cnt within measure across corpora'''
    obs = [[len(df_ee[df_ee['+/-']==1]),
            len(df_ee[df_ee['+/-']==2]),
            len(df_ee[df_ee['+/-']>2])], 
           [len(df_er[df_er['+/-']==1]),
            len(df_er[df_er['+/-']==2]),
            len(df_er[df_er['+/-']>2])], 
           [len(df_fc[df_fc['+/-']==1]),
            len(df_fc[df_fc['+/-']==2]),
            len(df_fc[df_fc['+/-']>2])]]
    chi2, p, dof, exp = scipy.stats.contingency.chi2_contingency(obs)
    print(title, chi2, p, dof)


def compare_valence_across_corpora(df_ee, df_er, df_fc, title):
    ''' compares #speakers per (non-0) valence within measure across corpora '''
    obs = [[len(df_ee[df_ee['pm_type']=='+']),
            len(df_ee[df_ee['pm_type']=='-']),
            len(df_ee[df_ee['pm_type']=='+/-'])], 
           [len(df_er[df_er['pm_type']=='+']),
            len(df_er[df_er['pm_type']=='-']),
            len(df_er[df_er['pm_type']=='+/-'])], 
           [len(df_fc[df_fc['pm_type']=='+']),
            len(df_fc[df_fc['pm_type']=='-']),
            len(df_fc[df_fc['pm_type']=='+/-'])]]
    chi2, p, dof, exp = scipy.stats.contingency.chi2_contingency(obs)
    print(title, chi2, p, dof)


def compare_sig_cnt_across_dc(df_ee, df_er, title):
    ''' compares #sig. speakers within measure across deception corpus '''
    obs = [[len(df_ee[df_ee['pm_type']!='0']),
            len(df_ee[df_ee['pm_type']=='0'])], 
           [len(df_er[df_er['pm_type']!='0']),
            len(df_er[df_er['pm_type']=='0'])]]
    chi2, p, dof, exp = scipy.stats.contingency.chi2_contingency(obs)
    print(title, chi2, p, dof)


def compare_sig_fea_cnt_across_dc(df_ee, df_er, title):
    ''' compares #speakers per sig. feature cnt within measure across XCDC '''
    obs = [[len(df_ee[df_ee['+/-']==1]),
            len(df_ee[df_ee['+/-']==2]),
            len(df_ee[df_ee['+/-']>2])], 
           [len(df_er[df_er['+/-']==1]),
            len(df_er[df_er['+/-']==2]),
            len(df_er[df_er['+/-']>2])]]
    chi2, p, dof, exp = scipy.stats.contingency.chi2_contingency(obs)
    print(title, chi2, p, dof)


def compare_sig_cnt_per_spk_type(df_lcon, df_syn, title):
    ''' compares #sig. speakers for lcon/syn across spk types '''
    df1 = df_lcon.copy()
    df2 = df_syn.copy()
    # only consider those with entrainment on at least one feature
    df1 = df1[df1['pm_type']!='0']
    df2 = df2[df2['pm_type']!='0']
    # compute count per speaker type
    df1['cnt'] = 1
    df2['cnt'] = 1
    grp_cols = ['gender', 'native_lang', 
                'gender_paired', 'native_lang_paired']
    df1 = df1.groupby(grp_cols).count()[['cnt']]
    df2 = df2.groupby(grp_cols).count()[['cnt']]
    # join to get results for both measures in same row and run test
    df = df1.join(df2, lsuffix='_syn', rsuffix='_con', how='outer').fillna(0)
    print(title, aux.ttest_rel(df['cnt_syn'], df['cnt_con']))


def compare_prtl_spk_types(df, col, levels, title, full_product=True):
    ''' compares #speakers per valence across partial speaker types

    partial speaker types only contain speaker & partner gender *or* native lang
    '''
    assert col in ['gender', 'native_lang'], 'col must be gender or native_lang'
    df = df.copy()
    # compute count per (partial) speaker type and valence    
    df['cnt'] = 1
    grp_cols = [col, col + '_paired', 'pm_type']
    df = df.groupby(grp_cols).count()[['cnt']]
    # ensure dataframe index contains all combinations of spk type & valence
    idx = itertools.product(levels, levels, ['+', '-', '+/-', '0'])
    if not full_product:
        # fisher corpus does not have chinese-chinese pairs; full_product flag
        # allows exclusion of those from calculation
        idx = list(idx)[4:]
    df = df.reindex(idx, fill_value=0)
    # group counts into 2d list of observations and run test
    obs = [df['cnt'][:4], df['cnt'][4:8], df['cnt'][8:12]]
    if full_product:
        obs.append(df['cnt'][12:])
    chi2, p, dof, exp = scipy.stats.contingency.chi2_contingency(obs)
    print(title, chi2, p, dof)
    return np.array(obs), exp


def get_ti_tf_ipus(df_bt):
    ''' limits "big table" to turn-initial and turn-final ipus '''
    # limit to turn exchanges, i.e., paired chunks
    df = df_bt[df_bt['p_or_x'] == 'p']
    # get all turn initial and turn final chunks in separate rows
    chu_ids_ti = list(df['chu_id'].values)
    chu_ids_tf = [int(v) for v in df['chu_id_paired'].values]
    df = df_bt[df_bt['chu_id'].isin(chu_ids_ti + chu_ids_tf)].copy()
    # add auxiliary column
    df['cnt'] = 1
    return df


def get_ipu_stats(df_rel, df_all, do_role_comp=False):
    ''' print stats for relevant (turn-initial/turn-final) and all ipus '''
    print('total number of relevant IPUs:', len(df_rel))
    print('syllables per relevant IPU: %.2f (%.2f)' %
          ((df_rel['rate_syl'] * df_rel['duration']).mean(),
           (df_rel['rate_syl'] * df_rel['duration']).std()))
    print('duration per relevant IPU (in s): %.2f (%.2f)' %
          (df_rel['duration'].mean(), df_rel['duration'].std()))
    print('total duration of relevant IPUs (in h): %.2f' %
          (df_rel['duration'].sum() / 3600))
    print('number of total IPUs per turn: %.2f (%.2f)' %
          (df_all.groupby('tur_id').count()['chu_id'].mean(),
           df_all.groupby('tur_id').count()['chu_id'].std()))
    # some counts are notably lower due to stricter handling of
    # null values than before (all features must now be not null)
    print('number of relevant IPUs per speaker:\n'
          '\tmin:  %.2f\n'
          '\tmax:  %.2f\n'
          '\tmean: %.2f\n'
          '\tstd:  %.2f\n\n' %
          (df_rel.groupby('spk_id').count()['cnt'].min(),
           df_rel.groupby('spk_id').count()['cnt'].max(),
           df_rel.groupby('spk_id').count()['cnt'].mean(),
           df_rel.groupby('spk_id').count()['cnt'].std()))
    print('speech rate of relevant IPUs per speaker: %.2f (%.2f)' %
          (df_rel.groupby('spk_id')['rate_syl'].mean().mean(),
           df_rel.groupby('spk_id')['rate_syl'].mean().std()))
    print('duration of relevant IPUs per speaker: %.2f (%.2f)' %
          (df_rel.groupby('spk_id')['duration'].mean().mean(),
           df_rel.groupby('spk_id')['duration'].mean().std()))
    get_syl_cnt = lambda x: x['rate_syl'] * x['duration']
    df_tmp = df_rel.groupby('spk_id').apply(get_syl_cnt)
    print('syllables per relevant IPU per speaker: %.2f (%.2f)\n\n' %
          (df_tmp.groupby('spk_id').mean().mean(),
           df_tmp.groupby('spk_id').mean().std()))
    _compare_binary(df_rel, 'gender', 'f', 'm')
    _compare_binary(df_rel, 'native_lang', 'Chinese', 'English')
    if do_role_comp:
        _compare_binary(df_rel, 'speaker_role', 'f', 'd')




