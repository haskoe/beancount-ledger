from collections import OrderedDict
from decimal import Decimal

VAT_PCT = Decimal("0.25")
VAT_FRACTION = VAT_PCT / (1 + VAT_PCT)

TEMPLATE_DIR = "templates"
GENERATED_DIR = "generated"

TAB = "\t"
COMMA = ","
DOT = "."
SEMICOLON = ";"

INCOME_SALG = "Income:Salg"
BANK_ERHVERV = "Assets:Bank:BankErhverv"

# CSV column names
DATE_POSTED = "date_posted"
ACCOUNT = "account"
AMOUNT_WITH_VAT = "amount_with_vat"
AMOUNT_VAT_FREE = "amount_vat_free"
AMOUNT_WO_VAT = "amount_wo_vat"
AMOUNT_WO_VAT_NEGATED = "amount_wo_vat_negated"
VAT = "vat"
VAT_NEGATED = "vat_negated"
AMOUNT = "amount"
AMOUNT_NEGATED = "amount_negated"
TOTAL_NEGATED = "total_negated"
POST_LINK = "post_link"
DESCRIPTION = "description"
TOTAL = "total"
ACCOUNT_NAME = "account_name"
ACCOUNT_GROUP = "account_group"
REGEX = "regex"
DATE_POSTED_KEY = "date_posted_key"

ANTAL_POSTERINGER = "ANTAL_POSTERINGER"
MED_MOMS = "med_moms"
UDEN_MOMS = "uden_moms"

ACCOUNT1 = "account1"
ACCOUNT2 = "account2"
ACCOUNT3 = "account3"
TRANSACTION_TYPE = "transaction_type"
TEXT = "text"
EXTRA_TEXT = "extra_text"
CURRENCY = "currency"
YYMM = "yymm"
YYMMDD = "yymmdd"
PERIOD_TXT = "period_txt"
HOURS = "hours"
SUPPORT_HOURS = "support_hours"
PRICE_TYPE = "price_type"
PRICE = "price"
VAT_NEGATED = "vat_negated"

AM_INDKOMST = "am_indkomst"
TIL_UDBETALING = "til_udbetaling"
LOEN_ATP = "LoenATP"
LOEN_SKAT = "LoenSkat"
LOEN_GEBYR = "LoenGebyr"
LOEN_ANSAT = "LoenAnsat"
AM_BIDRAG_MV = "AMBidragMV"
A_SKAT = "ASkat"

UDBYTTE = "udbytte"
UDBYTTE_SKAT_PCT = "udbytte_skat_pct"
# input filnavne
(
    UDGIFT_MEDMOMS_CSV,
    UDGIFT_CSV,
    BETALING_CSV,
    SALG_CSV,
    BANK_CSV,
    ACCOUNT_CSV,
    ACCOUNT_REGEX_CSV,
    BANK_TO_INVOICE_DATE_CSV,
    TRANSACTION_TYPE_CSV,
    SALG_TXT,
    PRICES_CSV,
    LOEN_CSV,
    UDBYTTE_CSV,
) = [
    "%s.csv" % (fn,)
    for fn in (
        "udgift_medmoms",
        "udgift",
        "betaling",
        "salg",
        "bank",
        "account",
        "account_regex",
        "bank_to_invoice_date",
        "transaction_type",
        "salg.txt",
        "prices",
        "loen",
        "udbytte",
    )
]


CSV_SPECS = OrderedDict(
    [
        (
            BANK_CSV,
            OrderedDict(
                [
                    (DATE_POSTED, str),
                    ("dummy", str),
                    (DESCRIPTION, str),
                    (AMOUNT, str),
                    (TOTAL, str),
                ]
            ),
        ),
        (
            ACCOUNT_CSV,
            OrderedDict(
                [
                    (ACCOUNT_NAME, str),
                    (ACCOUNT_GROUP, str),
                ]
            ),
        ),
        (
            ACCOUNT_REGEX_CSV,
            OrderedDict(
                [
                    (REGEX, str),
                    (ACCOUNT_NAME, str),
                ]
            ),
        ),
        (
            BANK_TO_INVOICE_DATE_CSV,
            OrderedDict(
                [
                    (DATE_POSTED_KEY, str),
                    (DESCRIPTION, str),
                    (ACCOUNT_NAME, str),
                ]
            ),
        ),
        (
            TRANSACTION_TYPE_CSV,
            OrderedDict(
                [
                    (ACCOUNT_GROUP, str),
                    (ANTAL_POSTERINGER, int),
                    (MED_MOMS, int),
                ]
            ),
        ),
        (
            SALG_TXT,
            OrderedDict(
                [
                    (ACCOUNT_NAME, str),
                    (YYMMDD, str),
                    (PERIOD_TXT, str),
                    (HOURS, float),
                    (SUPPORT_HOURS, float),
                ]
            ),
        ),
        (
            PRICES_CSV,
            OrderedDict(
                [
                    (ACCOUNT_NAME, str),
                    (PRICE_TYPE, str),
                    (YYMMDD, str),
                    (PRICE, str),
                ]
            ),
        ),
        (
            LOEN_CSV,
            OrderedDict(
                [
                    (DATE_POSTED, str),
                    (PERIOD_TXT, str),
                    (AM_INDKOMST, str),
                    (TIL_UDBETALING, str),
                    (LOEN_ATP, str),
                    (A_SKAT, str),
                    (AM_BIDRAG_MV, str),
                    (LOEN_GEBYR, str),
                    ("km", str),
                ]
            ),
        ),
        (
            UDBYTTE_CSV,
            OrderedDict(
                [
                    (UDBYTTE, str),
                    (UDBYTTE_SKAT_PCT, str),
                ]
            ),
        ),
    ]
)
# 0226	jan-feb	98694	59852.62	189.34	31233	7880	1	460.96

#                 d,txt,la,udb,atp,skat,am,gebyr,trans = [l[0], l[1]] + list(map(float,l[2:]))

# ;98694;59852.62;189.34;31233;7880;1;460.96
