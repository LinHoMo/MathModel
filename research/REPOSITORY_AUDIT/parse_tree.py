# -*- coding: utf-8 -*-
import json

with open(r'C:/Users/Lin/Desktop/Programs/MathModel/research/REPOSITORY_AUDIT/tree_main.json', encoding='utf-8') as f:
    data = json.load(f)

print('truncated:', data.get('truncated'))
items = data.get('tree', [])
print('total items:', len(items))
blobs = [i for i in items if i['type'] == 'blob']
trees = [i for i in items if i['type'] == 'tree']
print('blobs:', len(blobs), 'trees:', len(trees))
total_bytes = sum(i.get('size', 0) for i in blobs)
print('total bytes:', total_bytes)
for i in blobs:
    print('%8d  %s' % (i.get('size', 0), i['path']))
