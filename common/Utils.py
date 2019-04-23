def isEmpty(self, *values):
    for value in values:
        if value == '':
            return True
    return False
