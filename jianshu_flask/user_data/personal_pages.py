import time
import requests
from fake_useragent import UserAgent
from lxml import etree
from pymongo import MongoClient
# 连接数据库
client = MongoClient()
collection = client['Jshu']['jianshu']
# 准备请求头
BASE_HEADERS = {'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
                'Host': 'www.jianshu.com',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'text/html, */*; q=0.01',
                'User-Agent': UserAgent().random,
                'Connection': 'keep-alive',
                'Referer': 'http://www.jianshu.com'}


# 获取个人信息
class PersonalInformation:
    def __init__(self, slug):  # slug：用户标记
        self.headers = BASE_HEADERS
        self.slug = slug

    def basic_information(self):
        # 拼接个人页的url
        personal_url = 'https://www.jianshu.com/u/{}'.format(self.slug)
        # 发送请求获取响应数据
        response = requests.get(personal_url, headers=self.headers)
        # print(response.text)
        if response.status_code == '404':
            print('用户不存在，请重新输入')
        else:
            tree = etree.HTML(response.text)
            divs = tree.xpath('//div[@class="main-top"]')

            for div in divs:
                name = div.xpath('.//a[@class="name"]/text()')[0]
                head_pic = 'https:' + div.xpath('./a[1]/img/@src')[0]

                gender = div.xpath('./div/i/@class')
                # print('性别', gender)
                if gender:
                    gender = gender[0].split('-')[-1]
                    if gender == 'man':
                        gender = '男'
                    else:
                        gender = '女'
                else:
                    gender = '未知'

                is_contract = div.xpath('.//i[@class="iconfont ic-write"]/text()')
                if is_contract:
                    is_contract = '签约作者'
                else:
                    is_contract = 'No'

                info = div.xpath('.//li//p//text()')

                item = {
                    'name': name,
                    'slug': self.slug,
                    'head_pic': head_pic,
                    'gender': gender,
                    'is_contract': is_contract,
                    'following_num': int(info[0]),
                    'followers_num': int(info[1]),
                    'articles_num': int(info[2]),
                    'words_num': int(info[3]),
                    'be_liked_num': int(info[4]),
                    'update_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                }
                return item


# 获取个人动态信息
class PersonalDynamicInformation:
    def __init__(self, slug, update=False):
        self.slug = slug
        AJAX_HEADERS = {"Referer": "http//:www.jianshu.com/u/{slug}".format(slug=self.slug), "X-PJAX": "true"}
        self.headers = dict(BASE_HEADERS, **AJAX_HEADERS)
        # 初始化盛数据的容器：container
        self.container = {
            'comment_notes': [],  # 发表评论
            'like_notes': [],  # 喜欢文章
            'reward_notes': [],  # 赞赏文章
            'share_notes': [],  # 发表文章
            'like_users': [],  # 关注用户
            'like_colls': [],  # 关注专题
            'like_comments': [],  # 点赞评论
            'like_notebooks': [],  # 关注文集
        }
        # 更新动态
        if update:
            # 数据库中的最新动态时间：mongo_last_updated
            self.mongo_last_updated = collection.find_one({'slug': slug}, {'last_updated': 1}).get('last_updated')
        self.update = update

    # 获取动态
    def get_dynamics(self, id=None, page=1):
        if id == None:
            # 动态第一页
            url = 'http://www.jianshu.com/users/{slug}/timeline'.format(slug=self.slug)
        else:
            # 动态第二页之后需要依赖值id，可从前一页中取数据
            url = 'http://www.jianshu.com/users/{slug}/timeline?max_id={id}&page={page}'.format(slug=self.slug, id=id, page=page)
        print(url)
        # 发送请求获取响应数据
        response = requests.get(url, headers=self.headers)
        tree = etree.HTML(response.text)
        # 动态模块列表
        lis = tree.xpath('//ul[@class="note-list"]/li')
        if lis:
            # 最后更新时间
            last_updated = lis[0].xpath('.//span/@data-datetime')[0].split('+')[0].replace('T', ' ')
            if self.update == True:  # 更新
                # 如果最后更新时间与数据库时间一致，则停止爬取
                if last_updated == self.mongo_last_updated:
                    return self.container
            if page == 1:
                # 无论是否更新（避免多余判断），取出最新动态时间，更新到数据库
                self.container['last_updated'] = last_updated
                print(last_updated)

            for li in lis:
                # 时间
                mark_time = self.get_mark_time(li)
                if self.update == True:
                    if mark_time == self.mongo_last_updated:
                        return self.container
                    else:
                        self.parse_li(li, mark_time)
                else:
                    # 新增用户数据直接进行解析
                    self.parse_li(li, mark_time)
            # 抽取并计算得到下一页动态依赖的id
            last_li_id = lis[-1].xpath('@id')[0]
            next_first_id = int(last_li_id.split('-')[1]) - 1
            return self.get_dynamics(next_first_id, page + 1)
        else:
            # 页面为空，没更多的动态了
            return self.container

    # 解析li标签
    def parse_li(self, li, mark_time):
        l = li.xpath('.//span/@data-type')[0]
        # 发表评论
        if l == 'comment_note':
        # if li.xpath('.//span/@data-type')[0] == 'comment_note':
            comment_note = {}
            comment_note['comment_text'] = self.get_comment_text(li)  # 评论内容
            comment_note['time'] = mark_time  # 评论时间
            # comment_note['note_title'] = self.get_obj_title(li)
            comment_note['note_id'] = self.get_href_id(li)  # 文章id
            print('发表评论', comment_note)
            self.container['comment_notes'].append(comment_note)
        # 喜欢文章
        elif l == 'like_note':
        # elif li.xpath('.//span/@data-type')[0] == 'like_note':
            like_note = {}
            like_note['time'] = mark_time  # 时间
            # like_note['note_title'] = self.get_obj_title(li)
            like_note['note_id'] = self.get_href_id(li)  # 文章id
            print('喜欢文章', like_note)
            self.container['like_notes'].append(like_note)
        # 打赏
        elif l == 'reward_note':
            reward_note = {}
            reward_note['time'] = mark_time  # 打赏时间
            # reward_note['note_title'] = self.get_obj_title(li)
            reward_note['note_id'] = self.get_href_id(li)  # 文章id
            print('赞赏文章', reward_note)
            self.container['reward_notes'].append(reward_note)
        # 发表文章
        elif l == 'share_note':
            share_note = {}
            share_note['time'] = mark_time
            share_note['note_text'] = self.get_obj_text(li)
            share_note['note_id'] = self.get_href_id(li)
            print('发表文章', share_note)
            self.container['share_notes'].append(share_note)
        # 关注作者关注专题
        elif l == 'like_user':
            like_user = {}
            like_user['time'] = mark_time
            like_user['slug'] = self.get_href_id(li)
            print('关注作者', like_user)
            self.container['like_users'].append(like_user)
        # 关注专题
        elif l == 'like_collection':
            like_coll = {}
            like_coll['time'] = mark_time
            like_coll['coll_id'] = self.get_href_id(li)
            print('关注专题', like_coll)
            self.container['like_colls'].append(like_coll)
        # 点赞评论
        elif l == 'like_comment':
            like_comment = {}
            like_comment['time'] = mark_time
            like_comment['comment_text'] = self.get_comment_text(li)
            like_comment['slug'] = self.get_like_comment_slug(li)
            like_comment['note_id'] = self.get_like_comment_note_id(li)
            print('赞了评论', like_comment)
            self.container['like_comments'].append(like_comment)
        # 关注文集
        elif l == 'like_notebook':
            like_notebook = {}
            like_notebook['time'] = mark_time
            like_notebook['notebook_id'] = self.get_href_id(li)
            print('关注文集', like_notebook)
            self.container['like_notebooks'].append(like_notebook)
        # 加入简书
        elif l == 'join_jianshu':
        # elif li.xpath('.//span[@data-type="join_jianshu"]'):
            join_time = mark_time
            print('加入简书', join_time)
            self.container['join_time'] = join_time

    '''获取动态产生的时间'''
    def get_mark_time(self, li):
        mark_time = li.xpath('.//@data-datetime')[0].split('+')[0].replace('T', ' ')
        return mark_time

    '''获取文章标题'''
    def get_obj_title(self, li):
        title = li.xpath('.//a[@class="title"]/text()')[0]
        return title

    """获取文章内容"""
    def get_obj_text(self, li):
        text = li.xpath('.//p[@class="abstract"]/text()')[0]
        return text

    '''获取文章id'''
    def get_href_id(self, li):
        href_id = li.xpath('.//a[@class="title"]/@href')[0].split('/')[-1]
        return href_id

    '''获取发表评论的内容'''
    def get_comment_text(self, li):
        like_comment_text = ''.join(li.xpath('.//p[@class="comment"]/text()'))
        return like_comment_text

    '''获取被赞评论用户的slug'''
    def get_like_comment_slug(self, li):
        like_comment_slug = li.xpath('.//div[@class="origin-author single-line"]//@href')[0].split('/')[-1]
        return like_comment_slug

    '''获取评论文章的id'''
    def get_like_comment_note_id(self, li):
        like_comment_note_id = li.xpath('.//div[@class="origin-author single-line"]//@href')[1].split('/')[-1]
        return like_comment_note_id


# 获取全部信息
class AllInformation:
    # getallinfo() 分别处理首次抓取用户动态和更新用户动态
    def getallinfo(self, slug):
        if collection.find_one({'slug': slug}):
            print('该用户数据已经在数据库中', '\n', '正在更新数据……')
            # 更新用户信息
            baseinfo = PersonalInformation(slug).basic_information()
            if baseinfo:
                self.save_to_mongo(baseinfo, update=True)
                print('更新用户信息成功')
                timeline = PersonalDynamicInformation(slug, update=True).get_dynamics()
                if len(timeline) != 8:
                    # 如果timeline不为空
                    self.save_update_timeline(slug, timeline)
                    print('更新用户动态成功')
                else:
                    print('数据库中已是最新动态')
            else:
                error_info = '404,可能是因为您的链接地址有误、该文章已经被作者删除或转为私密状态。'
                self.save_error_txt(slug, error_info)
        else:
            info = PersonalInformation(slug)
            baseinfo = info.basic_information()
            if baseinfo:
                timeline = PersonalDynamicInformation(slug).get_dynamics()
                all_info = dict(baseinfo, **timeline)
                # print(all_info)
                self.save_to_mongo(all_info)
                print('存储用户信息成功')
            else:
                error_info = '404,可能是因为您的链接地址有误、该文章已经被作者删除或转为私密状态。'
                self.save_error_txt(slug, error_info)

    # 存储用户信息
    def save_to_mongo(self, all_info, update=False):
        if not update:
            collection.update({'slug': all_info['slug']}, {'$setOnInsert': all_info}, upsert=True)
        else:
            collection.update({'slug': all_info['slug']}, {'$set': all_info}, upsert=True)

    # 处理不存在的用户（被封禁等）的错误信息
    def save_error_txt(self, slug, error_info):
        with open('error.txt', 'a', encoding='utf-8') as f:
            f.write('http://www.jianshu.com/u/{0}'.format(slug) + ' ' + error_info + '\n')
            f.close()

    # 处理更新动态时的数据库操作(有$push操作，需单独写)
    def save_update_timeline(self, slug, timeline):
        collection.update({'slug': slug}, {'$set': {'latest_time': timeline['latest_time']}}, upsert=True)
        all_time = ['comment_notes', 'like_notes', 'reward_notes', 'share_notes',
                    'like_users', 'like_colls', 'like_comments', 'like_notebooks']
        for each_tag in all_time:
            if timeline[each_tag]:
                # $push是想列表尾部进行更新 $each是对传入的列表遍历
                collection.update({'slug': slug}, {'$push': {each_tag: {'$each': timeline[each_tag]}}})
                # {comment_notes:[{},{},{}]}


if __name__ == '__main__':
    # getinfo1 = PersonalInformation('ba17e5937433')
    # getinfo2 = PersonalDynamicInformation('ba17e5937433')
    # print(getinfo1.basic_information())
    # print(getinfo2.get_dynamics())
    getinfo = AllInformation()
    allinfo = getinfo.getallinfo('ba17e5937433')
    # allinfo = getinfo.getallinfo('5982f34347e7')












