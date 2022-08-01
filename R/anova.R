
# acoustic-prosodic features used as dependent variables below
features <- list(
    "df$intensity_mean",
    "df$intensity_max",
    "df$pitch_mean",
    "df$pitch_max",
    "df$jitter",
    "df$shimmer",
    "df$nhr",
    "df$rate_syl"
)

# independent variables (gender and native lang pairs) and their interaction
terms <- list(
    "df$g",
    "df$l",
    "df$g:df$l"
)

# runs anova on given dataframe for each acoustic feature
run_anovas <- function(df) {
    # treat independent variables as factors
    df$g <- as.factor(df$g)
    df$l <- as.factor(df$l)
    # run analysis for each feature
    for (feature in features) {
        frm <- paste(feature, " ~ df$g + df$l + df$g:df$l")
        print(frm)
        mod <- aov(formula(frm))
        print(summary(mod))
        cat("\n")
        for (i in 1:3) {
            # run post-hoc test for any term with p < 0.05
            if (summary(mod)[[1]][i,5] < 0.05) {
                print(TukeyHSD(mod, which=terms[[i]]))
                cat("\n")
            }
        }
        cat("\n\n\n")
    }
}
