



from collections import defaultdict


async def build_tree(items_list, id_key='id', parent_id="parent_id"):
    tag_dict, tag_tree = {}, defaultdict(list)
    for t in items_list:
        tag_dict[t[id_key]] = t
        tag_tree[t[parent_id]].append(t)
    for parent_id, items in tag_tree.items():
        parent = tag_dict.get(parent_id)
        if not parent: continue
        parent["children"] = items
    return tag_tree.pop(0, [])