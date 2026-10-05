from .branding import BRAND_NAME_AR, BRAND_NAME_EN, BRAND_TAGLINE


def brand(_request):
    return {
        "brand_name_ar": BRAND_NAME_AR,
        "brand_name_en": BRAND_NAME_EN,
        "brand_tagline": BRAND_TAGLINE,
    }
