import attr

@attr.s
class Vertex(object):
    name = attr.ib()
    text = attr.ib(default="")
    id = attr.ib(default="")


@attr.s
class Link(object):
    start = attr.ib(factory=Vertex)
    end = attr.ib(factory=Vertex)
    text = attr.ib(factory=str)
    type = attr.ib(default="arrow")
    stroke = attr.ib(default="thick")


class Graph(object):

    def __init__(self):
        self.vertices = {}
        self.edges = []
        self.missing_vertices = {}


    def add_vertex(self, vertex: Vertex, **kwargs):
        self.vertices[vertex.name] = dict(id=vertex.name, text=vertex.text)
        self.vertices[vertex.name].update(kwargs)


        self.missing_vertices.pop(vertex.name, None)

    def add_link(self, link: Link):

        if link.start.name not in self.vertices:
            self.missing_vertices[link.start.name] = ''
        if link.end.name not in self.vertices:
            self.missing_vertices[link.end.name] = ''

        self.edges.append(
            dict(start=link.start.name, end=link.end.name,
                 text=link.text, type=link.type,
                 stroke=link.stroke)
        )

    def get_vertex(self, name):
        if isinstance(name, Vertex):
            name = name.name
        return self.vertices.get(name)

    def get_vertex_obj(self, name):
        raw_vertex = self.get_vertex(name)

        # add name
        raw_vertex['name'] = name


        return Vertex(**raw_vertex)

    def get_edges(self):
        return self.edges

    def convert_dict_to_link(self, raw_link: dict) -> Link:
        raw_link['start'] = self.get_vertex_obj(raw_link['start'])
        raw_link['end'] = self.get_vertex_obj(raw_link['end'])
        return Link(**raw_link)


    def __eq__(self, other):
        return self.vertices == other.vertices and \
               self.edges == other.edges


def get_mermaid_link_line(link: Link):

    if link.stroke == "dotted":
        link_line = "-.->" if link.text == "" \
            else '-."{link_text}".->'.format(link_text=link.text)
    else:
        link_line = "==>" if link.text == "" \
            else '=="{link_text}"==>'.format(link_text=link.text)
    return " " + link_line + " "

def get_mermaid_node_text(vertex: Vertex):
    text = vertex.id if vertex.text == "" else \
        '{id}["{text}"]'.format(id=vertex.id, text=vertex.text)

    # replace new line with <br>
    text = text.replace('\n', '<br>')

    return text


def add_mermaid_node_text(vertex: Vertex, added_texts: list):
    if vertex.name in added_texts:
        text = vertex.name
    else:
        text = get_mermaid_node_text(vertex)
        added_texts.append(vertex.name)
    return text


def convert_graph_to_mermaid_text(graph: Graph) -> str:

    added_texts = []

    mermaid_text = "graph TD\n"

    for i in graph.get_edges():
        link = graph.convert_dict_to_link(i)

        # add firt node
        mermaid_text += add_mermaid_node_text(link.start, added_texts)

        # add link
        mermaid_text += get_mermaid_link_line(link)


        # add second node
        mermaid_text += add_mermaid_node_text(link.end, added_texts)

        # add end line
        mermaid_text += '\n'
    return mermaid_text
