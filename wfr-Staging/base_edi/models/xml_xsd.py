from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError

from lxml import etree as ET


class XmlTreeNode:

    def __init__(self, name, type, parent=None, min_occur=1, max_occur=1, ref=None):
        self.name = name
        self.type = type
        self.parent = parent
        self.children = []
        self.min_occur = min_occur
        self.max_occur = max_occur
        self.ref = ref

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name and self.type == other.type and self.min_occur == other.min_occur and \
            self.max_occur == other.max_occur and self.ref == other.ref and self.parent == other.parent

    def add_child(self, child):
        self.children.append(child)

    def remove_child(self, child):
        self.children.remove(child)

    def walk(self):
        yield self
        for child in self.children:
            yield from child

    def get_ref_name_children(self):
        res = []
        if self.ref:
            res.append(self)
        for child in self.children:
            res.extend(child.get_ref_name_children())
        return res

    def get_ref_type_children(self):
        res = []
        if self.type not in ['complex', 'decimal', 'date', 'int', 'string', 'boolean', 'time']:
            res.append(self)
        for child in self.children:
            res.extend(child.get_ref_type_children())
        return res

    def get_reference_children(self):
        return self.get_ref_name_children() + self.get_ref_type_children()


def _prepend_ns(ns, tag):
    return '{%s}%s' % (ns, tag)

class XmlXsd(models.Model):
    _name = 'xml.xsd'
    _description = 'XSD File'

    name = fields.Char('name')
    xsd_line_ids = fields.One2many(comodel_name='xml.xsd.line', string='XSD Lines', inverse_name='xsd_id')

    @api.model
    def create_from_xsd(self, name, file):
        def create_xsd_line(xsd, node, parent=None, sequence=1):
            vals = {
                'path': node.name,
                'type': node.type,
                'min_occur': node.min_occur,
                'max_occur': node.max_occur,
                'xsd_id': xsd.id,
                'sequence': sequence
            }
            if parent:
                vals.update(parent_id=parent.id)
            res = self.env['xml.xsd.line'].create(vals)
            sequence += 1
            for child in node.children:
                _, sequence = create_xsd_line(xsd, child, parent=res, sequence=sequence)
            return res, sequence

        res = self.create({
            'name': name,
        })
        tree = ET.fromstring(file)
        xsd_tree = self._parse_xml_file(tree)
        create_xsd_line(res, xsd_tree)
        return res

    @api.model
    def _parse_xml_file(self, tree):
        def descend_tree(node, parent=None):
            children = []
            xml_type = None
            if node.tag == _prepend_ns(ns_map['xs'], 'complexType'):
                children = node.findall('xs:sequence/*[@name]', namespaces=ns_map)
                xml_type = 'complex'
            elif node.tag == _prepend_ns(ns_map['xs'], 'element'):
                # This seems to be a limitation of the LXML library, that *[@name or @ref] doesn't work
                children += node.findall('xs:complexType/xs:sequence/*[@name]', namespaces=ns_map)
                children += node.findall('xs:complexType/xs:sequence/*[@ref]', namespaces=ns_map)
                children += node.findall('xs:complexType/xs:sequence/xs:choice/*[@name]', namespaces=ns_map)
                children += node.findall('xs:complexType/xs:sequence/xs:choice/*[@ref]', namespaces=ns_map)
                xsd_type = node.attrib.get('type')
                if xsd_type and ':' in xsd_type:
                    xsd_type = xsd_type.split(':')[-1]
                xml_type = xsd_type or 'complex'
            kwargs = {}
            if 'minOccurs' in node.attrib:
                kwargs.update(min_occur=int(node.attrib['minOccurs']))
            if 'maxOccurs' in node.attrib:
                max_occur = node.attrib['maxOccurs']
                kwargs.update(max_occur=-1 if max_occur == 'unbounded' else int(max_occur))
            if 'ref' in node.attrib:
                kwargs.update(ref=node.attrib['ref'])
            res = XmlTreeNode(node.attrib.get('name'), xml_type, parent=parent, **kwargs)
            for child_node in children:
                res.add_child(descend_tree(child_node, res))
            return res

        def merge_trees(parsed_trees):
            if not parsed_trees:
                return None
            reference_nodes = [
                child_node for parsed_tree in parsed_trees.values() for child_node in parsed_tree.get_reference_children()
            ]
            nonroot_partial_trees = {}
            for node in reference_nodes:
                parent = node.parent
                if node.ref:
                    parent.remove_child(node)
                    referenced = parsed_trees.pop(node.ref, nonroot_partial_trees.get(node.ref))
                    if node.ref not in nonroot_partial_trees:
                        nonroot_partial_trees[node.ref] = referenced
                    if referenced:
                        referenced.parent = parent
                        referenced.min_occur = node.min_occur
                        referenced.max_occur = node.max_occur
                        if parent:
                            parent.add_child(referenced)
                else:
                    referenced = parsed_trees.pop(node.type, nonroot_partial_trees.get(node.type))
                    if node.type not in nonroot_partial_trees:
                        nonroot_partial_trees[node.type] = referenced
                    node.type = 'complex'
                    for child in referenced.children:
                        child.parent = node
                        node.add_child(child)
            if len(parsed_trees) == 1:
                return parsed_trees.popitem()[1]
            elif len(parsed_trees) > 1:
                raise ValidationError('Too Many Root Nodes')
            else:
                raise ValidationError('Circular XSD Detected')

        possible_trees = {}
        ns_map = tree.nsmap
        for child in tree:
            res = descend_tree(child)
            possible_trees[res.name] = res
        final_tree = merge_trees(possible_trees)
        return final_tree


class XmlXsdLine(models.Model):
    _name = 'xml.xsd.line'
    _description = 'XSD File Line'
    _order = 'xsd_id, sequence'
    
    xsd_id = fields.Many2one(comodel_name='xml.xsd', string='XSD')
    parent_id = fields.Many2one(comodel_name='xml.xsd.line')
    child_ids = fields.One2many(comodel_name='xml.xsd.line', inverse_name='parent_id')
    path = fields.Char(string='Path', required=True)
    full_path = fields.Char(string='Full Path', compute='_compute_full_path', inverse='_set_full_path', recursive=True)
    required = fields.Boolean(string='Required', compute='_compute_required')
    min_occur = fields.Integer(string='Min Occurrences')
    max_occur = fields.Integer(string='Max Occurrences')
    type = fields.Selection(string='Type', selection=[('string', 'String'),
                                                      ('complex', 'Complex'),
                                                      ('decimal', 'Decimal Number'),
                                                      ('boolean', 'Boolean'),
                                                      ('int', 'Integer'),
                                                      ('time', 'Datetime'),
                                                      ('date', 'Date')])
    sequence = fields.Integer(string='Sequence', help='Determines the order when items are contained in a sequence')

    # _sql_constraints = [
    #     ('path_unique', 'check UNIQUE(xsd_id, parent_id, path)', 'This path already exists')
    # ]

    @api.depends('min_occur')
    def _compute_required(self):
        for line in self:
            line.required = line.min_occur >= 1

    @api.depends('path', 'parent_id.full_path')
    def _compute_full_path(self):
        for line in self:
            if not line.parent_id:
                line.full_path = line.path
            else:
                line.full_path = '%s/%s' % (line.parent_id.full_path, line.path)

    def _set_full_path(self):
        for line in self:
            components = line.full_path.split('/')
            parent_paths = components[:-1]
            first_parent = parent_paths[0] if parent_paths else None
            node = line.xsd_id.xsd_line_ids.filtered_domain([('path', '=', first_parent), ('parent_id', '=', False)])
            for parent in parent_paths[:1]:
                next_node = node.child_ids.filtered_domain([('path', '=', parent)])
                if not next_node:
                    raise UserError(_('Node %s/%s does not exist' % (node.full_path, parent)))
                node = next_node
            line.path = components[-1]
            line.parent_id = node

    def name_get(self):
        return self.mapped(lambda line: (line.id, line.path))
