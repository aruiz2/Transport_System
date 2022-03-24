class mParser():
    def __init__(self, file):
        self.file = file
        self.__get_data()

    def __get_data(self):
        f = open(self.file, 'r')
        lines = f.readlines()[1:-3] #remove irrelevant data
        f.close()

        #get hostname
        port_assignment = lines[0].split(':')
        self.hostname = (port_assignment[1].split(',')[0])

        #get peers
        peers_assignment = lines[1].split(':')
        self.peers = int(peers_assignment[1].split(',')[0])

        #get content_info
        cinfo_assignment = lines[2].split(':')
        cinfo_assignment = cinfo_assignment[1].split(',')
        cinfo_assignment[0] = cinfo_assignment[0][3:-1]; cinfo_assignment[1] = cinfo_assignment[1][2:-2]
        self.content_info = [cinfo_assignment[0], cinfo_assignment[1]]

        self.__get_peer_data(lines[3:])

    def __get_peer_data(self, lines):
        peer_info = lines[1:]
        peers_info_list = []
        curr_dict = {}; n = len(peer_info)

        #update peer data
        for i in range(2, n):
            curr_str = peer_info[i]
            curr_data = curr_str.split(':')
            key = curr_data[0][2:-1]

            if key != "content_info":
                val = int(curr_data[1][1:-2])
                curr_dict[key] = val

            else: 
                val = []
                list_val =  curr_data[1].split(',')
                j = 0
                for word in list_val:
                    #first item
                    if word[0:2] == " [":
                        word = word[3:-1]; val.append(word)
                    #last item
                    elif word[-1] == '\n':
                        word = word[2:-3]; val.append(word)
                    
                    #rest of items
                    else:
                        word = word[2:-1]; val.append(word)

                key = curr_data[0][2:-1]
                curr_dict[key] = val

                #append the dictionary and clear curr_dict for the next peer
                peers_info_list.append(curr_dict)
                curr_dict = {}
        
        self.peer_info = peers_info_list