from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from pyecharts import WordCloud
from pymongo import MongoClient

from user_data.analysis import AnalysisUser

client = MongoClient()
collection = client['Jshu']['jianshu']
app = Flask(__name__)


# @app.route('/', methods=['GET', 'POST'])
# def index():
#     """
#     如果为get请求显示首页
#     如果为post请求
#         先获取数据
#         信息存在跳转详情页
#         不存在返回首页，显示错误字段
#     """
#     if request.method == 'GET':
#         return render_template('index.html')
#     else:
#         name = request.form.get('url')
#         # print(name)
#         ret = collection.find_one({'name': name})
#         # print(ret)
#         if ret:
#             info = {}
#             info['head_pic'] = ret['head_pic']
#             info['name'] = ret['name']
#             info['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             info['like_users_num'] = ret['following_num']
#             info['followers_num'] = ret['followers_num']
#             info['share_notes_num'] = ret['articles_num']
#             info['words_num'] = ret['words_num']
#             info['be_liked_num'] = ret['be_liked_num']
#             return render_template('detail.html', baseinfo=info)
#         else:
#             return render_template('index.html', error_msg='你输入用户名不存在，请重新输入')

@app.route('/', methods=['POST', 'GET'])
def geturl():
    if request.method == 'POST':
        slug = request.form['url']
        if slug:
            return redirect(url_for('jianshu_timeline', slug=slug))
        else:
            return render_template('index.html', error_msg='请输入数据！')
    return render_template('index.html')

@app.route('/timeline')
def jianshu_timeline():
    slug = request.args.get('slug')
    user = AnalysisUser(slug)
    baseinfo = user.get_baseinfo()
    comments = user.get_comment()
    share = user.get_share()

    return render_template('detail.html',
                           baseinfo=baseinfo,
                           comments_num=comments[0],
                           share_num=share[0],
                           s_wordcloud_chart=s_make_wordcloud(share[1]),
                           c_wordcloud_chart=c_make_wordcloud(comments[1])
                           )


def c_make_wordcloud(comm_data):
    '''
    用pyecharts绘制词云图
    :param comm_data:
    :return:
    '''
    # name 词语的列表
    name = comm_data.keys()

    # value 次数的列表
    value = comm_data.values()

    # 绘制词云图片
    # 生成词云对象
    wordcloud = WordCloud(width='100%', height=600)

    # 通过词云对象调用add() 第一个参数是图片名字, 词语列表, 词频列表, shape形状,
    wordcloud.add("", name, value, shape="diamond", word_size_range=[15, 50])

    # 词云对象.render_embed()
    return wordcloud.render_embed()


def s_make_wordcloud(comm_data):
    '''
    用pyecharts绘制词云图
    :param comm_data:
    :return:
    '''
    # name 词语的列表
    name = comm_data.keys()

    # value 次数的列表
    value = comm_data.values()

    # 绘制词云图片
    # 生成词云对象
    wordcloud = WordCloud(width='100%', height=600)

    # 通过词云对象调用add() 第一个参数是图片名字, 词语列表, 词频列表, shape形状,
    wordcloud.add("", name, value, shape="pentagon", word_size_range=[15, 50])

    # 词云对象.render_embed()
    return wordcloud.render_embed()


if __name__ == '__main__':
    app.run(debug=True)