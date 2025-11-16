quests = {'1': {'text': '123'}, '2': {'text': '123123'}}
# , '3': {'text': '121231233'}, '4': {'text': ''}, '5': {'text': ''}, '6': {'text': ''}, '7': {'text': ''}, '8': {'text': ''}
class TEST:
    def __init__(self, data, data2 = None):
        self.data = data
        self.data2 = data2
        print(self.data, self.data2)

test = TEST(data=key, data2=value ) for key, value in quests.items()

# print([{key: value} for key, value in quests.items()])