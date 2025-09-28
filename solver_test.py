from ocr import load_grid_from_csv
from solver import Solver, Strand

def test_solve():
    grid = load_grid_from_csv("./puzzles/example.csv")
    solver = Solver(grid)
    solution = solver.solve()
    assert solution == [
        Strand(positions=[(0, 0), (1, 0), (2, 0), (3, 0)], string='WORD'),
        Strand(positions=[(0, 1), (1, 1), (2, 1), (3, 1)], string='TEST'),
        Strand(positions=[(0, 2), (1, 2), (2, 2), (3, 2)], string='COOL'),
        Strand(positions=[(0, 3), (1, 3), (2, 3), (3, 3)], string='EASY')
    ]

def test_find_words_no_min_length():
    grid = load_grid_from_csv("./puzzles/2025-09-14.csv")
    solver = Solver(grid)
    words = solver.find_words(current_pos=(0, 0), min_length=0)
    words_str = {w.string for w in words}
    assert words_str == {
        "TED",
        "THEY",
        "THE",
        "TH",
        "TEAL",
        "TEHSIL",
        "TESS",
        "THEA",
        "TEAD",
        "TEADISH",
        "TEDA",
        "T",
        "TEA",
        "THY",
        "TE",
        "TEASLE",
        "TSS",
        "TSH",
        "TESLA",
        "TSA",
    }


def test_find_words():
    grid = load_grid_from_csv("./puzzles/2025-09-14.csv")
    solver = Solver(grid)
    words = solver.find_words(current_pos=(0, 0))
    words_str = {w.string for w in words}
    assert words_str == {
        "THEY",
        "TEAL",
        "TEHSIL",
        "TESS",
        "THEA",
        "TEAD",
        "TEADISH",
        "TEDA",
        "TESLA",
        "TEASLE",
    }


def test_find_all_words():
    grid = load_grid_from_csv("./puzzles/2025-09-14.csv")
    solver = Solver(grid)
    words = solver.find_all_words()
    words_str = {w.string for w in words}
    # fmt: off
    assert words_str == {"SLOG", "SIXTE", "ADAI", "KODA", "GOTE", "LOTE", "ONSIDE", "DISHY", "POSEY", "RELAIS", "RESET", "GUSTOISH", "LOSSES", "OAST", "REUEL", "FUSE", "AERY", "TOILER", "ERASER", "GONY", "SOWEL", "SIER", "SAXTIE", "SISAL", "OSSET", "DOSS", "WALK", "TIER", "SITE", "SARE", "ASUR", "SASH", "TEEL", "WODGY", "SESS", "ROTE", "REIT", "AIOLI", "DYAS", "SALT", "SHED", "ODETS", "YEST", "LASIX", "SLAIT", "TESLA", "OUST", "ROID", "ADITI", "SUIT", "OADAL", "USAR", "KEYWAY", "TONSIL", "DIGOR", "AYIN", "SERE", "LEER", "LION", "URSA", "SLED", "ALOD", "DALO", "ADLAI", "USED", "NOESIS", "EURO", "NOTE", "AXITE", "WASH", "SEARY", "ASHE", "LUST", "FEDERAL", "ADET", "REET", "SEIT", "FLOG", "WASHED", "FESTINO", "LEONIS", "WELS", "LADER", "SODA", "FOGY", "DIOL", "HEADY", "SISE", "RULY", "SESIA", "STEEL", "SLADE", "DOKO", "AXISED", "SLARE", "ELDEST", "TIAR", "WODE", "LIDE", "DEFUSION", "SALE", "SAYID", "ROTSE", "ROIL", "SLUGGISH", "LINO", "ELIOT", "AXED", "YEES", "EAST", "TEREUS", "SUET", "LOST", "SLOE", "STEROL", "TIDY", "STERO", "SERO", "IDEAL", "ESTH", "SEDILE", "UREAL", "HEAL", "STOLE", "AXIS", "SEARED", "ROIST", "AITION", "RASE", "DEAFLY", "ONSET", "TOLE", "LODE", "NIDAL", "SEROLIN", "LADIN", "LOGWAY", "YASHT", "STEROIDAL", "WADE", "LOGGIN", "GOLF", "INSEA", "SNORE", "SODY", "ESSAY", "REOIL", "ERADE", "SHEA", "RULE", "LEISURELY", "URASE", "STEAL", "YESO", "SYED", "LOUSE", "RESEDA", "SODIO", "DESITION", "OSTIAL", "TEADISH", "FLOE", "GILO", "WELK", "NILE", "ALOSE", "LEARY", "ILEON", "FLOGSTER", "SILO", "YEDO", "OLID", "OXEA", "SEELY", "DAER", "REDE", "FEAL", "EASEL", "RALE", "RESALE", "TSIA", "RAISED", "NITO", "TINY", "DEAL", "SEXTON", "FLOUSE", "DITE", "URSAL", "AWOKE", "RETIA", "ISUROID", "ADESITE", "ASHET", "SOLA", "HEDGY", "ELODEA", "FESTILOGY", "SEAX", "UREASE", "REASY", "DESALT", "LOSE", "SISTER", "RAISE", "RADA", "SLEY", "INLET", "SOLE", "SEALERY", "ASSET", "EASIER", "WOKE", "TEDA", "LITSEA", "FESTE", "SNOT", "WAYSIDE", "ARED", "LEASER", "ORLE", "DASH", "LISH", "ROLE", "SERON", "LASSO", "SEAR", "USER", "EASY", "DEALER", "LADINO", "OUSTER", "DAWES", "YOLK", "SALEP", "YADE", "ODESA", "LOAF", "SLAW", "EASE", "OASES", "NOISE", "FAST", "EULYSITE", "DAIS", "LASI", "RUSA", "TISAR", "SEPOY", "RETINOL", "WUGG", "WALE", "RELAXED", "SURELY", "SIDA", "EYRA", "LYSIS", "SOGGY", "DIGS", "FOSTER", "EXIT", "STOGY", "ADAR", "EXTER", "ASIO", "SION", "DARYL", "FUSTEE", "DALK", "STEY", "STELIS", "OSLO", "DEASH", "FEAR", "EYRE", "SILESIA", "TIDAL", "TINO", "GOEL", "SOUSE", "LEAD", "LEDE", "USTER", "READ", "ODIN", "ESTERLIN", "UREY", "POESY", "ARYL", "WAYS", "FUSED", "RELY", "STEADY", "ELSA", "DEXTER", "DALT", "SEDER", "DITER", "IDOSE", "SEDITION", "LEWD", "SEXTILE", "ALOW", "YESSO", "THEY", "FUGGY", "NOTER", "REUSE", "LEES", "TONY", "SOFA", "ISURET", "SELT", "LOGY", "HEST", "NITER", "SUITE", "SOLAY", "LOUSY", "EASER", "EXITION", "STION", "ASHY", "FUSION", "SNITE", "SYRE", "RESISTER", "WADI", "YALE", "OTIS", "STORE", "IAEA", "DOES", "FADER", "LUES", "YITE", "FLYWAY", "REAL", "OGDOAS", "IDOL", "LAET", "LITER", "LOWA", "SLOD", "ASHES", "LAIUS", "AXION", "GORE", "DOSSAL", "RURAL", "RESEE", "SERAL", "EPOS", "RELISH", "ADION", "LOTI", "SUER", "LARS", "LOXIA", "LIDA", "RESUIT", "ELIDE", "ALEP", "YOKEL", "LEON", "STEROID", "RULER", "LINY", "RELOT", "AEDES", "SURA", "DAYS", "ALSO", "WASTED", "TESS", "DEFUSE", "SLAE", "DESI", "SISEL", "GILES", "INSET", "ARSYL", "NOISEFUL", "RETIARY", "STOREY", "ALOE", "YAWY", "STEELY", "DILO", "AEDILE", "OTIDES", "ADELA", "LURE", "ASOK", "LYGUS", "TILE", "SELION", "LORE", "ELYSIA", "SLASH", "IOLITE", "STOLID", "SESTI", "ELOD", "POKE", "SUSI", "LOIN", "SESTIAD", "SUWE", "IDEA", "LARUS", "OSTEOID", "GOAD", "OSSAL", "LOADS", "SUIST", "TOIL", "DEAR", "LOWY", "GULOSE", "SALSA", "IONI", "SIST", "ESOP", "SLUG", "TELI", "WASE", "LIGYDA", "DOLA", "ILOT", "FOGGISH", "LYRA", "LOADER", "SEXIST", "ALKES", "SNIG", "SEXT", "ASSE", "ERASION", "GONITIS", "ERASE", "REDEAL", "SUITOR", "DESSA", "ELOISE", "NOISY", "SELAR", "HESS", "SIDES", "ESSAYISH", "SEKOS", "EXALT", "LEONID", "SALSE", "YELK", "DESS", "FOSITE", "EDESTIN", "DOSA", "LADY", "SADE", "PEWY", "SOLES", "IDOLA", "IDES", "ELSE", "GOLI", "LURA", "STERE", "ARUI", "ADIN", "WASHY", "DWALE", "ARSE", "ELODES", "SOPE", "FOGGY", "SIDY", "ODAL", "SITIO", "REESE", "EELY", "AOUL", "STONISH", "FUST", "EXITE", "AFEARED", "LOGIN", "LOAD", "ESOX", "GULO", "EXISTER", "ARES", "SLOW", "RESALT", "DOKE", "KOAE", "SEALER", "DESTINY", "DALE", "KOEL", "LYSE", "EYAS", "SERAX", "SNOG", "LEISURED", "WALES", "LASER", "TEIOID", "EARED", "LUSIAD", "YEEL", "LASSET", "DESIST", "UREA", "SOKE", "TEAD", "STID", "LOSS", "OUSE", "LERESIS", "NIOG", "GONYS", "ERASURE", "SEALED", "OTIDAE", "EXTOL", "DEALT", "GULF", "SLEW", "ITER", "RAIS", "RESEISE", "RUER", "ISERE", "AWOL", "ORLET", "ELON", "OPEL", "TEER", "ERSE", "LESION", "STEER", "ELUSION", "SESTOLE", "LURAL", "WASTE", "SADITE", "ALDER", "FUSTIN", "ASEA", "LASS", "RESEAL", "DARES", "TORU", "NOIL", "TIDE", "LINSEY", "SAXIST", "FADE", "RELAX", "SLASHED", "ERAL", "ADIT", "DIOR", "STILE", "ALOES", "GORLIN", "ODESSA", "DOWEL", "RUSE", "LUGOSI", "RAIU", "EDGY", "LOGGISH", "GOITER", "FOGUS", "RESIST", "SEISE", "LADE", "SEER", "GOER", "LEISURE", "OSTIARY", "SERAI", "GOAF", "LIDO", "LOINS", "SETH", "DISH", "HEAD", "LEROT", "EDIYA", "AION", "ARSIS", "EDWY", "PESO", "GISH", "DEFOUL", "SNIT", "TORE", "RASER", "SLAY", "FEST", "AFEAR", "OSIER", "EDEA", "RESISTOR", "SOUL", "YULE", "URESIS", "RASION", "AXIOLITE", "SIAL", "LOUSTER", "LITE", "LETO", "IONISED", "SERA", "SEAL", "REES", "SAFE", "SALK", "SIONITE", "SAITE", "NOEL", "EDITOR", "WOAD", "IONISE", "SLASHY", "RELADE", "SLUGGY", "GOLEE", "LOIS", "FOSIE", "TEHSIL", "YUIT", "TOISE", "SULFA", "REEL", "LEADS", "DESYL", "TEAL", "ALOWE", "NILOT", "LAXIST", "SEEL", "LADYISH", "SEXTO", "DASHY", "DILOGY", "OILER", "TONISH", "POSE", "DAISY", "TIGON", "EDITION", "DALER", "NYSE", "LUIS", "RESUE", "SHEAL", "AIEL", "RASURE", "LISE", "FOUL", "OSELA", "SUSIE", "SALES", "GIDE", "POKEY", "STONY", "OSSE", "TILER", "LEET", "SNIDE", "TEREU", "SURAL", "FUYE", "SLOKE", "YETH", "GONYDEAL", "EUROTIALES", "DASYUROID", "NIDE", "LAST", "GUSTO", "WUST", "URALS", "SEXTOLE", "DEARY", "WOADY", "RELISHY", "ISRAEL", "LEONIDAS", "RAIOID", "SEDGY", "DEAF", "DION", "GOETIA", "LEAR", "ADINOLE", "LEASE", "GOES", "ESTOILE", "USEE", "SEOUL", "FUGO", "SILE", "LUITE", "SIGYN", "SOLFA", "URAL", "TORUS", "ROIT", "DASYURE", "REIS", "EASED", "AFOUL", "OUSEL", "OKEY", "SILOIST", "DOLE", "RETIAL", "FEARED", "STEADYISH", "SLAD", "SIDE", "FLUSTER", "YEAST", "KOLA", "FEAST", "ELINOR", "EXIST", "FESTER", "ALERSE", "OSTIOLE", "EDIT", "ESTER", "AEOLUS", "YERE", "EULER", "AXES", "LOKE", "HYADES", "POSY", "TEASLE", "ILEUS", "DARE", "ESERE", "LUSTER", "RETIN", "LAOS", "LEDA", "THEA", "SOULY", "STEAD", "GUST", "EROTESIS", "TOGS", "WAST", "STOG", "ALODY", "NOILER", "SADO", "YOKE", "USTION", "LOITER", "OLEO", "RAISER", "LASH", "SIOL", "DOSE", "OXTER", "SAXE", "SETON", "LOTS", "DASI", "TONS", "SURE", "GONID", "SLAISTER", "LYRE", "GUFA", "ETIOLIN", "DEFOG"}
    # fmt: on
