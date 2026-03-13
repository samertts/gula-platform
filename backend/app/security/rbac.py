
roles={

"admin":["all"],

"doctor":["read","write"],

"lab":["read"],

"citizen":["self"]

}

def check(role,action):

    if "all" in roles.get(role,[]):

        return True

    return action in roles.get(role,[])

