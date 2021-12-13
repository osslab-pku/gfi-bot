import gfibot.data.rest as rest


def test_page_num():
    assert rest.get_page_num(30, 90) == 3
    assert rest.get_page_num(30, 91) == 4
