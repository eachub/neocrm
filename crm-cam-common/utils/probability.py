#!D:python3
# -*- coding: utf-8 -*-
# @Time : 2/8/22 4:54 PM
# @Author : yahui
import numpy as np
import numpy.random as npr
from decimal import Decimal


class AliasMethods(object):

    @staticmethod
    def alias_setup(probs):
        '''
        probs： 某个概率分布
        返回: Alias数组与Prob数组
        '''
        K = len(probs)
        # if not probs or not isinstance(probs, list):
        #     raise Exception(f"probs: {probs} type must be list")

        if 1*10000 - sum([Decimal(str(_i))*10000 for _i in probs]):
            raise Exception("probability sum not equals 1")

        prob_array = np.zeros(K)  # 对应Prob数组
        alias_array = np.zeros(K, dtype=np.int)  # 对应Alias数组
        # Sort the data into the outcomes with probabilities
        # that are larger and smaller than 1/K.
        smaller = []  # 存储比1小的列
        larger = []  # 存储比1大的列
        for kk, prob in enumerate(probs):
            prob_array[kk] = K * Decimal(str(prob))  # 概率
            if prob_array[kk] < 1.0:
                smaller.append(kk)
            else:
                larger.append(kk)

        # Loop though and create little binary mixtures that
        # appropriately allocate the larger outcomes over the
        # overall uniform mixture.

        # 通过拼凑，将各个类别都凑为1
        while len(smaller) > 0 and len(larger) > 0:
            small = smaller.pop()
            large = larger.pop()

            alias_array[small] = large  # 填充Alias数组
            prob_array[large] = prob_array[large] - (1.0 - prob_array[small])  # 将大的分到小的上

            if prob_array[large] < 1.0:
                smaller.append(large)
            else:
                larger.append(large)
        print(alias_array, prob_array)
        return alias_array, prob_array

    @staticmethod
    def alias_draw(alias, prob, random_1, random_2):
        '''
        输入: Prob数组和Alias数组,随机数1，随机数2
        输出: 一次采样结果
        '''
        K = len(alias)
        # Draw from the overall uniform mixture.
        kk = int(np.floor(random_1 * K))  # 随机取一列

        # Draw from the binary mixture, either keeping the
        # small one, or choosing the associated larger one.
        if random_2 < prob[kk]:  # 比较
            return kk
        else:
            return alias[kk]

    @staticmethod
    def alias_draw_auto(alias, prob):
        '''内部生成随机数'''
        K = len(alias)
        kk = int(np.floor(npr.rand() * K))  # 随机取一列
        if npr.rand() < prob[kk]:  # 比较
            return kk
        else:
            return alias[kk]


if __name__ == '__main__':
    obj = AliasMethods()
    # 初始概率配置
    probs = np.array([0.23, 0.1, 0.67])
    alias_a, prob_a = obj.alias_setup(probs)
    result = list()
    # 抽样100次
    for i in range(100):
        ret = obj.alias_draw_auto(alias_a, prob_a)
        # ret = obj.alias_draw(alias_a, prob_a, npr.rand(), npr.rand())
        result.append(ret)

    # 抽奖结果统计
    for i in range(3):
        print(f"{i} ==> count {result.count(i)}")
