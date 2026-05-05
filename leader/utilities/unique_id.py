import uuid

# While uuid.uuid4() is very unlikely to hit a duplicate id, this makes it literally impossible for greater robustness
def unique_id(data):
    unique=False        
    id = ""

    while(not unique):
        id = str(uuid.uuid4())
        u = True
        for id_t in data["ids"]:
            if id_t == id:
                u = False

        unique = u

    data["ids"].append(id)
    return id
