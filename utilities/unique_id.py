import uuid

def unique_id(data):
    unique=False        
    id = ""

    while(not unique):
        id = uuid.uuid4()
        u = True
        for id_t in data["ids"]:
            if id_t == id:
                u = False

        unique = u

    data["ids"].append(id)
    return id