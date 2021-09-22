# Useful Neo4j Queries
## Files that will be compile in all pathes
match p=(t:Target {name: "Tutorial"})-[*0..]->(:Literal)
with nodes(p) as ns
where NONE(node in ns where node:Select)
return ns

# Files that will be compile if USE_MYMATH is true
match p=(t:Target {name: "Tutorial"})-[*0..]->(:Select {condition: "(USE_MYMATH)"})-[:TRUE]->()-[*0..]->(:Literal)
return p

# Files that will be compile if USE_MYMATH is false
match p=(t:Target {name: "Tutorial"})-[*0..]->(:Select {condition: "(USE_MYMATH)"})-[:FALSE]->()-[*0..]->(:Literal)
return p

# Condition it's value which contain MakeTable.cxx file from Tutorial
match (:Target {name: "Tutorial"})-[*0..]->(s:Select)-[r]->()-[*0..]->(l:Literal {name: "MakeTable.cxx"})
return s.condition,type(r)