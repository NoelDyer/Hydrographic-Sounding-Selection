from sounding_selection.node import Node
from sounding_selection.characterdimensions import *
from shapely.geometry import Point


class Tree(object):
    """Creates Class Tree"""
    def __init__(self, c):
        self.__root = Node()
        self.__capacity = c

    def get_root(self):
        return self.__root

    def get_leaf_threshold(self):
        return self.__capacity

    def build_point_tree(self, point_set):
        for i in range(point_set.get_vertices_num()):
            self.insert_vertex(self.__root, 0, point_set.get_domain(), i, point_set)

    def insert_vertex(self, node, node_label, node_domain, v_index, tin):
        if node_domain.contains_point(tin.get_vertex(v_index), tin.get_domain().get_max_point()):
            if node.is_leaf():
                if node.is_duplicate(v_index, tin):
                    return
                node.add_vertex(v_index)  # update append list
                if node.overflow(self.__capacity):
                    # WE HAVE TO RAISE A SPLIT OPERATION
                    # current node become internal, and we initialize its children
                    node.init_sons()
                    for i in node.get_vertices():
                        self.insert_vertex(node, node_label, node_domain, i, tin)
                    node.reset_vertices()  # empty the list of the current node

            else:  # Internal
                mid_point = node_domain.get_centroid()
                for i in range(4):
                    s_label, s_domain = node.compute_son_label_and_domain(i, node_label, node_domain, mid_point)
                    self.insert_vertex(node.get_son(i), s_label, s_domain, v_index, tin)

    def generalize(self, node, node_label, node_domain, target_v, point_set, deletes, scale, h_spacing, v_spacing):
        if node is None:
            return
        else:
            search_window = get_character_dimensions(target_v, scale, h_spacing, v_spacing)[0]

            if node.is_leaf():
                if node.get_vertices_num() == 0:
                    pass
                else:
                    delete_list = {}
                    for v_id in node.get_vertices():
                        v = point_set.get_vertex(v_id)
                        if v != target_v:
                            s_point = Point(v.get_x(), v.get_y())
                            if search_window.intersects(s_point):
                                target_label = get_character_dimensions(target_v, scale, h_spacing, v_spacing)[1]
                                if target_label.intersects(s_point) and target_v.get_z() < v.get_z():
                                    # z-value precision issue: use '<=' to remove initial legibility violations
                                    delete_list[v_id] = v
                                else:
                                    v_label = get_character_dimensions(v, scale, h_spacing, v_spacing)[1]
                                    if target_label.intersects(v_label) and target_v.get_z() < v.get_z():
                                        # z-value precision issue: use '<=' to remove initial legibility violations
                                        delete_list[v_id] = v

                    for v_id in delete_list:
                        node.remove_vertex(v_id)
                        deletes.append(delete_list[v_id])

            else:  # Internal
                # we visit the sons in the following order: NE -> NW -> SW -> SE
                mid_point = node_domain.get_centroid()
                for i in range(4):
                    s_label, s_domain = node.compute_son_label_and_domain(i, node_label, node_domain, mid_point)
                    if s_domain.contains_polygon(search_window):
                        self.generalize(node.get_son(i), s_label, s_domain, target_v, point_set, deletes, scale,
                                        h_spacing, v_spacing)
                        break
                    elif s_domain.intersects_polygon(search_window):
                        self.generalize(node.get_son(i), s_label, s_domain, target_v, point_set, deletes, scale,
                                        h_spacing, v_spacing)

    def get_points_in_polygon(self, node, node_label, node_domain, polygon, source_point_set, point_list):
        if node is None:
            return
        else:
            if node.is_leaf():
                if node.get_vertices_num() == 0:
                    pass
                else:
                    for v_id in node.get_vertices():
                        v = source_point_set.get_vertex(v_id)
                        s_point = Point(v.get_x(), v.get_y())
                        if polygon.intersects(s_point):
                            point_list.append(v)

            else:  # Internal
                # we visit the sons in the following order: NE -> NW -> SW -> SE
                mid_point = node_domain.get_centroid()
                for i in range(4):
                    s_label, s_domain = node.compute_son_label_and_domain(i, node_label, node_domain, mid_point)
                    if s_domain.contains_polygon(polygon):
                        self.get_points_in_polygon(node.get_son(i), s_label, s_domain, polygon, source_point_set,
                                                   point_list)
                        break
                    elif s_domain.intersects_polygon(polygon):
                        self.get_points_in_polygon(node.get_son(i), s_label, s_domain, polygon, source_point_set,
                                                   point_list)
