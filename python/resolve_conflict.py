import numpy as np
import dendropy
import math
from dendropy.simulate import treesim
import random
from dendropy import Tree
import matplotlib.pyplot as plt
from operator import itemgetter, attrgetter
import math
import pandas as pd
from collections import Counter


tips_number = 10
alignment_len = 5000
recom_len = 500
threshold_len = 200
recom_rate = .05
max_tMRCA= 0.01
nu_ex = 0.2
# nu_in = 0.1
internal = 1
leaf = 1

taxon_list= []
for i in range(tips_number):
  taxon_list.append(str(i))
taxa = dendropy.TaxonNamespace(taxon_list)


clonal_tree = '(((((6:0.001446144501320992,1:0.001446144501320992):0.000858783257504586,0:0.002304927758825578):0.0037305214882076792,5:0.006035449247033257):0.0015612289512319762,(9:0.007254085544720213,8:0.007254085544720213):0.000342592653545021):0.002403321801734765,((7:9.5535429188809e-05,3:9.5535429188809e-05):0.0007261022934883541,(4:0.00023702151844960976,2:0.00023702151844960976):0.0005846162042275533):0.009178362277322836):0.0;'
recomtrees = ['(((((6:0.002304927758825578,0:0.002304927758825578)11:0.0037305214882076792,5:0.006035449247033257)12:0.0015612289512319762,(9:0.007254085544720213,8:0.007254085544720213)13:0.000342592653545021)14:0.002403321801734765,((7:9.5535429188809e-05,3:9.5535429188809e-05)15:0.0007261022934883541,(4:0.00023702151844960976,2:0.00023702151844960976)16:0.0005846162042275533)17:0.009178362277322836)18:0.0938183816331946,1:0.1038183816331946);\n', '((((0:0.006035449247033257,5:0.006035449247033257)12:0.0015612289512319762,(9:0.007254085544720213,8:0.007254085544720213)13:0.000342592653545021)14:0.002403321801734765,((7:9.5535429188809e-05,3:9.5535429188809e-05)15:0.0007261022934883541,(4:0.00023702151844960976,2:0.00023702151844960976)16:0.0005846162042275533)17:0.009178362277322836)18:0.0940371955604373,(6:0.001446144501320992,1:0.001446144501320992)10:0.1025910510591163);\n']
recomnodes = [1, 10]


# ----------------------------------------------------------------------------------------------------------------------
def set_index(tree):
    for node in tree.postorder_node_iter():
      node.index = -1
      node.annotations.add_bound_attribute("index")

    s = len(tree.leaf_nodes())
    for node in tree.postorder_node_iter():
      if not node.is_leaf():
          node.index = s
          node.label = str(node.index)
          s += 1
      else:
          node.index = node.taxon.label
          node.label = str(node.index)
# ----------------------------------------------------------------------------------------------------------------------
def resolve_parent_nodes(s_equ, tree, temptree):
    desc = []
    n = []
    length = []
    tip_len = []
    for i in range(len(s_equ)):
        my_node = int(s_equ[i][0])
        # print(my_node)
        if my_node >= tips_number:
            res = set()
            desc.append(give_descendents(tree, my_node, res))
            n.append(my_node)
            length.append(s_equ[i][2])
            tip_len.append(temptree.find_node_with_label(str(int(s_equ[i][1]))).distance_from_tip())

    for i in range(len(desc)):
        for j in range(len(s_equ)):
            if (int(s_equ[j][0]) < tips_number) and (int(s_equ[j][0]) in desc[i]):
                tmp = list(desc[i])
                # print(int(s_equ[j][0]) , list(desc[i]) , n[i])
                for k in range(len(tmp)):
                    print(tmp[k], tmp[k], length[i] + tip_len[i], n[i])

    return desc
# ----------------------------------------------------------------------------------------------------------------------
def resolve_conflict(clonaltree, recomtrees, recomnodes):
    conflict = common_nodes(clonaltree, recomnodes)
    # print(recomnodes)
    if len(conflict) > 0:
        for i in range(len(conflict)):
            # print(conflict[i][0], conflict[i][1])
            node1 = clonaltree.find_node_with_label(str(conflict[i][0]))
            node2 = clonaltree.find_node_with_label(str(conflict[i][1]))
            if node1.parent_node == node2:
                id_main = recomnodes.index(conflict[i][1])
                id_temp = recomnodes.index(conflict[i][0])
                maintree = Tree.get_from_string(recomtrees[id_main], schema='newick')
                set_index(maintree)
                temptree = Tree.get_from_string(recomtrees[id_temp], schema='newick')
                set_index(temptree)

                if int(node1.index) < tips_number:
                    # print("node is taxa")
                    prunenode = maintree.find_node_with_label(str(node1.index))
                    recomnode = temptree.find_node_with_label(str(node1.index))
                else:
                    # print("node is internal")
                    res = set()
                    desc = give_descendents(clonaltree, node1.index, res)
                    prune_index = my_mrca(maintree, list(desc))
                    prunenode = maintree.find_node_with_label(str(prune_index))
                    recom_index = my_mrca(temptree, list(desc))
                    recomnode = temptree.find_node_with_label(str(recom_index))

                # print(maintree.as_ascii_plot())
                # print(maintree.as_string(schema="newick"))
                # print("prunenode:")
                # print(prunenode)
                # print(prunenode.edge_length)
                # print("recomnode:")
                # print(recomnode)
                # print(recomnode.edge_length)
                parent = prunenode.parent_node
                # print("parent")
                # print(parent)

                if ((recomnode.edge_length) > parent.distance_from_tip()) and ((recomnode.edge_length) < maintree.max_distance_from_root()):
                    maintree.prune_subtree(prunenode)  # the original recombinant node was removed to reinsert in the other side

                    res = set()
                    desc = give_descendents(clonaltree, node2.index, res)
                    d = list(desc)
                    random_node = np.random.choice(taxon_list,replace=False)
                    while int(random_node) in d:
                        random_node = np.random.choice(taxon_list,replace=False)
                    candidatenode = maintree.find_node_with_label(str(random_node))

                    attached_node, attached_id, ancestor = find_attached_node(maintree, recomnode, candidatenode)

                    relocated_nodes = ancestor[attached_id - 1]  # relocated node is the adjacent node of recombinant node
                    attached_node.remove_child(relocated_nodes)  # relocated node was removed to reinsert in to right side
                    newborn = dendropy.datamodel.treemodel.Node()  # newborn in the new mrca of recombinant node and its sister
                    newborn.add_child(recomnode)
                    if attached_node.edge_length is None:
                        attached_node.edge_length = 0
                    newborn.edge_length = maintree.max_distance_from_root() - (recomnode.edge_length + attached_node.edge_length)
                    relocated_nodes.edge_length = relocated_nodes.edge_length - newborn.edge_length
                    newborn.add_child(relocated_nodes)
                    attached_node.add_child(newborn)



                    print(maintree.as_string(schema="newick"))
                    print(maintree.as_ascii_plot())




# ----------------------------------------------------------------------------------------------------------------------
def common_nodes(clonaltree,overlap_nodes):
  kids = []
  nodes = []
  s_overlap_nodes = np.sort(overlap_nodes)
  for i in range(len(s_overlap_nodes)):
    nodes.append(s_overlap_nodes[i])
    if s_overlap_nodes[i] >= tips_number:
      desc = set()
      kids.append(give_descendents(clonaltree,s_overlap_nodes[i],desc))
    else:
      kids.append({(s_overlap_nodes[i])})

  subsets = []
  for i in range(len(kids)):
    for j in range(i+1,len(kids)):
      if (kids[i].issubset(kids[j])):
        # print(i,j)
        subsets.append([nodes[i], nodes[j]])

  return subsets
# ----------------------------------------------------------------------------------------------------------------------
def give_descendents(tree,node_index,result):
  if node_index >= tips_number:
    internal_recom_node = tree.find_node_with_label(str(node_index))
    children = internal_recom_node.child_nodes()
    for n in range(len(children)):
      r_node= int(children[n].index)
      if r_node >= tips_number:
        give_descendents(tree,r_node,result)
      else:
        result.add(r_node)
  return result

# ----------------------------------------------------------------------------------------------------------------------
def merge_Recomtrees(recomtrees , recomnodes):

  clonaltree = Tree.get_from_string(clonal_tree,schema='newick')
  set_index(clonaltree)

  # if one one node is the subset of the other nodes
  conflict = common_nodes(clonaltree,recomnodes)

  if (len(conflict) > 0)  and (conflict[0][0] == conflict[0][1]):
        print("Same nodes")
        conflict = []

  if len(conflict) == 0 :
      print("NOOOOOO conflict!")

      desc = []
      equ = np.zeros((len(recomtrees),4))
      for treeid in range(len(recomtrees)):
        rtree= Tree.get_from_string(recomtrees[treeid],schema='newick')
        set_index(rtree)
        equ[treeid,0] = recomnodes[treeid]
        equ[treeid,1:3] = give_equivalent_node(rtree)
        equ[treeid,3] = treeid

      s_equ = equ[equ[:,2].argsort()[::-1]]
      s_equ = give_older_recom(s_equ)
      # print(s_equ)

      maintree = Tree.get_from_string(recomtrees[int(s_equ[0][3])],schema='newick')
      set_index(maintree)

      for i in range(1,len(s_equ)):
        temptree = Tree.get_from_string(recomtrees[int(s_equ[i][3])],schema='newick')
        set_index(temptree)
        node_maintree = int(s_equ[i][0])
        if node_maintree  >= tips_number:
          node_maintree = new_mrca(clonaltree,maintree,node_maintree,int(s_equ[i-1][0]))
        prunenode = maintree.find_node_with_label(str(node_maintree))
        node = temptree.find_node_with_label(str(int(s_equ[i][1])))
        parent = prunenode.parent_node

        attached_node,attached_id,ancestor =  find_attached_node(maintree,node,prunenode)
        regraft_recomnodes(maintree,attached_node,attached_id,prunenode,node,ancestor)

      return maintree.as_string(schema="newick")

  elif len(conflict) > 0 :
    print("CONFLICT!! ")
    for i in range(len(conflict)):
      if conflict[i][0] < tips_number:
        print("one node is taxa!")
      else:
        print("two nodes are internal!")
# ----------------------------------------------------------------------------------------------------------------------
def new_mrca(tree1,tree2,primenode,deletenode):
  a = []
  desc = set()
  d = give_descendents(tree1,primenode,desc)
  rlist = set()
  removelist = give_descendents(tree1,deletenode,rlist)
  if len(removelist)> 0 :
    a = [x for x in d if x not in removelist]
  else:
    a = list(d)
  final_node = my_mrca(tree2,a)
  return final_node

# ----------------------------------------------------------------------------------------------------------------------
def my_mrca(tree,tips):
  pdm = tree.phylogenetic_distance_matrix()
  taxon = tree.taxon_namespace
  node0 = [i for i,x in enumerate(taxon) if x.label==str(tips[0])]
  node1 = [i for i,x in enumerate(taxon) if x.label==str(tips[len(tips)-1])]
  myMrca = pdm.mrca(taxon[node0[0]], taxon[node1[0]])

  return myMrca.index

# ----------------------------------------------------------------------------------------------------------------------

def regraft_recomnodes(tree,attached_node,attached_id,prunenode,recomnode,ancestor):
  relocated_nodes = ancestor[attached_id-1]  # relocated node is the adjacent node of recombinant node
  tree.prune_subtree(prunenode) # the original recombinant node was removed to reinsert in the other side
  attached_node.remove_child(relocated_nodes) # relocated node was removed to reinsert in to right side
  newborn = dendropy.datamodel.treemodel.Node()  # newborn in the new mrca of recombinant node and its sister
  newborn.add_child(prunenode)
  prunenode.edge_length = recomnode.edge_length
  if attached_node.edge_length is None:
    attached_node.edge_length = 0
  newborn.edge_length = tree.max_distance_from_root() - (recomnode.edge_length + attached_node.edge_length)
  relocated_nodes.edge_length = relocated_nodes.edge_length - newborn.edge_length
  newborn.add_child(relocated_nodes)
  attached_node.add_child(newborn)
#   --------------------------------------------------------------------------------------------------------------------
def give_equivalent_node(recomtree):
  e = []
  for edge in recomtree.postorder_edge_iter():
    if edge.length is None:
      edge.length = 0
    e.append(edge.length)

  m = np.max(e)
  for node in recomtree.postorder_node_iter():
    if node.edge_length == m and node.is_leaf():
      return node.label,m
    elif node.edge_length == m and node.is_internal():
      return node.label,node.distance_from_tip() + m

# ----------------------------------------------------------------------------------------------------------------------
def find_attached_node(tree,node,prunenode):
  if ((node.edge_length) < tree.max_distance_from_root()) :
    ancestor = []
    for id,tmp_node in enumerate(prunenode.ancestor_iter()):
        ancestor.append(tmp_node)
        if node.edge_length < tmp_node.distance_from_tip() :
            attached_node = tmp_node
            attached_id = id
            break
  return attached_node,attached_id,ancestor

# ----------------------------------------------------------------------------------------------------------------------
def give_older_recom(s_equ):
  count = Counter(a[0] for a in s_equ)
  max = np.max([a[2] for a in s_equ])
  [a for a in s_equ if (count[a[0]] == 1) or (a[2]==max)]
  return [a for a in s_equ if (count[a[0]] == 1) or (a[2]==max)]

# ----------------------------------------------------------------------------------------------------------------------



initialTree = Tree.get_from_string(clonal_tree,schema='newick')
set_index(initialTree)

merge_Recomtrees(recomtrees,recomnodes)

resolve_conflict(initialTree,recomtrees,recomnodes)