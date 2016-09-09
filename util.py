# -*- coding: utf-8 -*-
import math


def cosine_similarity(v1,v2):
    sumxx, sumxy, sumyy = 0, 0, 0
    for i in range(len(v1)):
        x = v1[i]; y = v2[i]
        sumxx += x*x
        sumyy += y*y
        sumxy += x*y
    return sumxy/math.sqrt(sumxx*sumyy)


def mean_similarity(v1, v2):
    ratios = []
    for i in range(len(v1)):
        ratios.append(abs(v1[i] - v2[i]))
    return 100 - sum(ratios) / len(ratios)


def humanize_ibm_output(output):

    human_output = {
        'personality': {},
        'needs': {},
        'values': {}
    }

    def build_dict(source):
        result = dict()
        for i in source:
            result[i['name']] = {
                'percentage': i['percentage'] * 100,
                'sampling_error': i['sampling_error'],
                'children': {}
            }
            if 'children' in i:
                for j in i['children']:
                    result[i['name']]['children'][j['name']] = {
                        'percentage': j['percentage'] * 100,
                        'sampling_error': j['sampling_error']
                    }
        return result

    tmp = output['tree']['children'][0]['children'][0]['children']
    human_output['personality'] = build_dict(tmp)

    tmp = output['tree']['children'][1]['children'][0]['children']
    human_output['needs'] = build_dict(tmp)

    tmp = output['tree']['children'][2]['children'][0]['children']
    human_output['values'] = build_dict(tmp)

    return human_output
