from django.core.urlresolvers import resolve
from django.test import TestCase
from django.http import HttpRequest
from django.template.loader import render_to_string

from .views import home_page
from .models import Item, List


class HomePageTest(TestCase):
    # URL의 사이트 루트("/")를 해석해서 특정 뷰 기능에 매칭시킬 수 있는지 테스트
    def test_root_url_resolves_to_home_page_view(self):
        found = resolve('/')
        self.assertEqual(found.func, home_page)

    # 이 뷰 기능이 특정 HTML을 반환하게 해서 기능 테스트를 통과할 수 있는지 테스트
    def test_home_page_returns_correct_html(self):
        request = HttpRequest()

        response = home_page(request)
        expected_html = render_to_string('home.html')

        self.assertEqual(response.content.decode(), expected_html)


class NewListTest(TestCase):
    # POST 요청 처리 테스트 / 아이템 입력이 잘 되는지 테스트
    def test_saving_a_POST_request(self):
        self.client.post(
            '/lists/new',
            data={'item_text': '신규 작업 아이템'}
        )

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, '신규 작업 아이템')

    # Post 요청 응답 후, 리다이렉션 & 적절한 상태코드 테스트
    def test_redirects_after_POST(self):
        response = self.client.post(
            '/lists/new',
            data={'item_text': '신규 작업 아이템'}
        )
        new_list = List.objects.first()
        self.assertRedirects(response, '/lists/%d/' % (new_list.id))


class ListAndItemModelTest(TestCase):

    def test_saving_and_retrieving_items(self):
        list_ = List()
        list_.save()

        first_item = Item()
        first_item.text = '첫 번째 아이템'
        first_item.list = list_
        first_item.save()

        second_item = Item()
        second_item.text = '두 번째 아이템'
        second_item.list = list_
        second_item.save()
        saved_list = List.objects.first()
        self.assertEqual(saved_list, list_)

        saved_items = Item.objects.all()
        self.assertEqual(saved_items.count(), 2)

        first_saved_item = saved_items[0]
        second_saved_item = saved_items[1]
        self.assertEqual(first_saved_item.text, '첫 번째 아이템')
        self.assertEqual(first_saved_item.list, list_)
        self.assertEqual(second_saved_item.text, '두 번째 아이템')
        self.assertEqual(second_saved_item.list, list_)


class ListViewTest(TestCase):

    def test_uses_list_template(self):
        list_ = List.objects.create()
        response = self.client.get('/lists/%d/' % (list_.id))
        self.assertTemplateUsed(response, 'list.html')

    def test_displays_only_items_for_that_list(self):
        correct_list = List.objects.create()
        Item.objects.create(text='아이템 1', list=correct_list)
        Item.objects.create(text='아이템 2', list=correct_list)
        other_list = List.objects.create()
        Item.objects.create(text='다른 목록 아이템 1', list=other_list)
        Item.objects.create(text='다른 목록 아이템 2', list=other_list)       

        # Django TestCase의 테스트 클라이언트 사용
        response = self.client.get('/lists/%d/' % (correct_list.id))

        self.assertContains(response, '아이템 1')
        self.assertContains(response, '아이템 2')
        self.assertNotContains(response, '다른 목록 아이템 1')
        self.assertNotContains(response, '다른 목록 아이템 2')


class NextItemTest(TestCase):
    # POST를 이용해서 새로운 아이템을 기존 목록에 추가하는 URL을 만듦
    def test_can_save_a_POST_request_to_an_existing_list(self):
        other_list = List.objects.create()
        correct_list = List.objects.create()

        self.client.post(
            '/lists/%d/add_item' % (correct_list.id),
            data={'item_text': '기존 목록에 신규 아이템'}
        )

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, '기존 목록에 신규 아이템')
        self.assertEqual(new_item.list, correct_list)

    def test_redirects_to_list_view(self):
        correct_list = List.objects.create()

        response = self.client.post(
            '/lists/%d/add_item' % (correct_list.id),
            data={'item_text': '기존 목록에 신규 아이템'}
        )
    
        self.assertRedirects(response, '/lists/%d/' % (correct_list.id))

    def test_passes_correct_list_to_template(self):
        correct_list = List.objects.create()
        other_list = List.objects.create()
        response = self.client.get('/lists/%d/' % (correct_list.id))
        self.assertEqual(response.context['list'], correct_list)