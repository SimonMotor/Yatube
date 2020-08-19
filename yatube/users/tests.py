from django.test import TestCase, Client

class PageTest(TestCase):

    def test_page_404(self):
        response = Client().get('/page_blablabla/')
        self.assertEqual(response.status_code, 404)
        print(f'{response.status_code} = 404')
