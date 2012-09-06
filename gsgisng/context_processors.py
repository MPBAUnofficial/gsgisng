from local_settings import HOME_PAGE_ID

def home_page_id(context):
    """
    Gives to templates the variable HOME_PAGE_ID
    """
    return {'HOME_PAGE_ID':HOME_PAGE_ID}
