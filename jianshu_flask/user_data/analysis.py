from collections import Counter

import jieba
from pymongo import MongoClient

from user_data.personal_pages import AllInformation


class AnalysisUser:
    def __init__(self, slug):
        self.client = MongoClient()
        self.db = self.client['Jshu']['jianshu']
        self.slug = slug
        user_data = self.db.find_one({'slug': self.slug})
        # 一个用户的所有信息的字典
        update = True
        if user_data and update == False:
            '''如果指定不更新数据且数据已经在mongodb中'''
            self.user_data = user_data
        else:
            '''获取或更新数据到mongodb中'''
            AllInformation().getallinfo(slug)
            # 数据去了哪里?MongoDB
            '''从mongodb中取出该用户的数据'''
            self.user_data = self.db.find_one({'slug': self.slug})
            # self.user_data --> 就是一个用户的所有信息
            print(self.user_data)

    # 获取基本信息
    def get_baseinfo(self):
        baseinfo = {
            'head_pic': self.user_data['head_pic'],
            'name': self.user_data['name'],
            'update_time': self.user_data['update_time'],
            'like_users_num': self.user_data['following_num'],
            'followers_num': self.user_data['followers_num'],
            'share_notes_num': self.user_data['articles_num'],
            'words_num': self.user_data['words_num'],
            'be_liked_num': self.user_data['be_liked_num'],
            'like_notes_num': len(self.user_data['like_notes']),
            'like_colls_num': len(self.user_data['like_colls']),
            'like_nbs_num': len(self.user_data['like_notebooks']),
            'comment_notes_num': len(self.user_data['comment_notes']),
            'like_comments_num': len(self.user_data['like_comments']),
            'reward_notes_num': len(self.user_data['reward_notes'])
        }
        print(baseinfo)
        return baseinfo

    # 文章分词
    def get_share(self):
        # 抽出所有评论，进行词频统计，得出该用户评论中最常用的词，为绘制成词云做准备
        share = self.user_data['share_notes']
        # text：一个所有评论的列表
        text = []
        for c in share:
            text.append(c['note_text'])
        # share_text：所有评论的字符串
        share_text = ''.join(text)
        # print(share_text)
        # share_text_list：分词后的列表
        share_text_list = jieba.lcut(share_text)
        # 排序并且取出前150个
        freq = Counter(share_text_list).most_common(150)
        # share_word：对词语进行统计 --> 字典{词语:数量}
        share_word = {x[0]: x[1] for x in freq if len(x[0]) >= 2}
        # hot_comments = [{'name':list(comm_word.keys())[i],'value':list(comm_word.values())[i]}
        #                 for i in range(len(comm_word))]
        print(share_word)
        # 返回的是评论数量,返回统计分词的字典
        return [len(text), share_word]

    # 评论分词
    def get_comment(self):
        # 抽出所有评论，进行词频统计，得出该用户评论中最常用的词，为绘制成词云做准备
        comments = self.user_data['comment_notes']
        # text：一个所有评论的列表
        text = []
        for c in comments:
            text.append(c['comment_text'])
        # comm_text：所有评论的字符串
        comm_text = ''.join(text)
        # comm_text_list：分词后的列表
        comm_text_list = jieba.lcut(comm_text)
        # 排序并且取出前150个
        freq = Counter(comm_text_list).most_common(150)
        # comm_word：对词语进行统计 --> 字典{词语:数量}
        comm_word = {x[0]: x[1] for x in freq if len(x[0]) >= 2}
        # hot_comments = [{'name':list(comm_word.keys())[i],'value':list(comm_word.values())[i]}
        #                 for i in range(len(comm_word))]
        print(comm_word)
        # 返回的是评论数量,返回统计分词的字典
        return [len(text), comm_word]


if __name__ == '__main__':
    slug = 'ba17e5937433'
    # slug = '5982f34347e7'

    user = AnalysisUser(slug)
    user.get_baseinfo()
    user.get_comment()
    user.get_share()






