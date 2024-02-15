import re
from appinfo import App

class Phrase(object):

    def __init__(self,predicate_num):
        self.predicate_num = predicate_num
        self.subject_num = -1
        self.condition_num = -1
        self.object_num = -1
        self.proposition_num = -1
        self.private_condition_num = -1
        self.condition_list = []
        self.relation_list = []
        self.predicate_list =[]
        self.predicate_list.append(predicate_num)
        self.subject_list =[]
        self.object_list =[]
        self.private_condition_list =[]
        self.text = ""
        self.true_flag = True
        

    
    def print(self):
        print("subject:"+str(self.subject_list)+",predicate:"+str(self.predicate_list)+",object:"+str(self.object_list)+",condition:"+str(self.condition_list))

class Converter(object):

    def __init__(self,root_path,app_path,rule_name):
        self.all_phrase_list:Phrase = []
        self.proposition_list = []
        self.root_path = root_path
        self.app = App(app_path)
        self.rule_name = rule_name
        import stanza
        
        stanza.install_corenlp()
        stanza.download('en', proxies=proxies)
        self.nlp = stanza.Pipeline('en',
                            processors='tokenize,pos,lemma,depparse')

    def checkduplicate(self,text):
        proposition_num = 0
        find_flag = False
        for proposition in  self.proposition_list:
            if proposition == text:
                return_proposition_num = proposition_num
                find_flag = True
            proposition_num = proposition_num + 1
        if find_flag==False:
            self.proposition_list.append(text)
            return_proposition_num = proposition_num
        return return_proposition_num
        
    def text_to_formula(self,long_text):
        if long_text.replace(" ","").startswith("\""):
            proposition_num = self.checkduplicate(long_text)
            formula = "P"+str(proposition_num)
            return formula

        formula = ""
        or_lists = long_text.split(",")
        for text in or_lists:
            if "\"" in text:
                proposition_num = self.checkduplicate(text)
                formula = formula+"P"+str(proposition_num)+" & "
                continue
            phrases = self.stanza_text_to_ltl(text)
            for phrase in phrases:
                if phrase.true_flag == True:
                    formula = formula+"P"+str(phrase.proposition_num)+" & "
                else:
                    formula = formula+"!P"+str(phrase.proposition_num)+" & "
            if len(phrases)>0:
                formula = formula[0:len(formula)-3]+" & "
        if len(or_lists)>0:
            formula = formula[0:len(formula)-3]
        return formula

    def convert_file(self):
        path=self.root_path+"define/"+self.app.app_name+"/"
        f = open(path+self.rule_name+"english_specifications.txt",'r',encoding='utf-8')
        f_o = open(path+self.rule_name+"LTL_specifications.txt",'w',encoding='utf-8')
        pattern1 = "(.*)->(.*)if(.*)before(.*), then(.*)"
        pattern2 = "(.*)-> if(.*)before(.*), then(.*)"
        pattern3 = "(.*)-> After(.*),(.*), and after(.*), (.*)"
        pattern4 = "(.*)-> After(.*?), then(.*)"
        lines=f.readlines()
        self.formula_list = []
        for line in lines:
            formula = ""
            matchObj1 = re.match( pattern1, line)
            matchObj2 = re.match( pattern2, line)
            matchObj3 = re.match( pattern3, line)
            matchObj4 = re.match( pattern4, line)
            if matchObj2:
                formula = "!G(!"+self.text_to_formula(matchObj2.group(3))+" & "+self.text_to_formula(matchObj2.group(2))+" & X("+self.text_to_formula(matchObj2.group(1))+") -> X("+self.text_to_formula(matchObj2.group(4))+"))"
            elif matchObj1:
                formula = "!G("+self.text_to_formula(matchObj1.group(1))+" -> "+self.text_to_formula(matchObj1.group(2))+") & G("+self.text_to_formula(matchObj1.group(1).replace(matchObj1.group(4),""))+" & "+self.text_to_formula(matchObj1.group(3))+" & X("+self.text_to_formula(matchObj1.group(1))+") -> X("+self.text_to_formula(matchObj1.group(5))+"))"
            elif matchObj3:
                formula = "!G("+self.text_to_formula(matchObj3.group(1))+" -> ("+self.text_to_formula(matchObj3.group(2))+" -> "+self.text_to_formula(matchObj3.group(3))+")) & !G("+self.text_to_formula(matchObj3.group(3))+" -> ("+self.text_to_formula(matchObj3.group(4))+" -> "+self.text_to_formula(matchObj3.group(5))+"))"
            elif matchObj4:
                formula = "!G("+self.text_to_formula(matchObj4.group(1))+" -> ("+self.text_to_formula(matchObj4.group(2))+" -> "+self.text_to_formula(matchObj4.group(3))+"))"
            elif "->" in line:
                text = line.split("->")
                formula = "!G("+self.text_to_formula(text[0])+" -> "+self.text_to_formula(text[1])+")"
            else:
                formula = "!G("+self.text_to_formula(line)+")"
            self.formula_list.append(formula.replace(" ",""))
            print("Line:"+line)
            print("Formula:"+formula)
            f_o.write("Line:"+line)
            f_o.write("Formula:"+formula.replace(" ","")+"\n\n")
            f_o.flush()
        proposition_num = 0
        for proposition in self.proposition_list:
            f_o.write("P"+str(proposition_num)+":"+proposition+"\n")
            proposition_num=proposition_num+1
        for formula in self.formula_list:
            f_o.write(formula+"\n")
        f_o.close()
    
    def stanza_text_to_ltl(self,text):
        from stanza.server.ud_enhancer import UniversalEnhancer
        with UniversalEnhancer(language="en") as enhancer:
            doc = self.nlp(text)
            result = enhancer.process(doc)
            sentence_num = -1
            for sentence_result in result.sentence:
                phrase_list=[]
                sentence_num = sentence_num+1
                dependencies = sentence_result.enhancedDependencies
                
                sentence_text = doc._sentences[sentence_num]
                word_num=1
                all_word = ""
                for word in sentence_text.words:
                    all_word=all_word+str(word_num)+":"+word.text+", "
                    word_num=word_num+1
                print(all_word)
                # print(dependencies.edge)
                for edge in dependencies.edge:
                    for phrase in phrase_list:
                        phrase.print()
                    print(edge)
                    find_flag = False
                    phrase1 = None
                    phrase2 = None
                    if "parataxis" in edge.dep or "conj" in edge.dep:
                        print("1 branch")
                        for phrase in phrase_list:
                            if phrase.predicate_num == edge.source:
                                phrase1 = phrase
                            elif phrase.predicate_num == edge.target:
                                phrase2 = phrase
                        if phrase2==None and phrase1==None:
                            continue
                        if phrase1==None:
                            phrase1 = Phrase(edge.source)
                            phrase_list.append(phrase1)
                        if phrase2==None:
                            phrase2 = Phrase(edge.target)
                            phrase_list.append(phrase2)
                        if phrase1.condition_list!= [] and phrase2.condition_list== []:
                            phrase2.condition_list = phrase1.condition_list
                        elif phrase1.condition_list!= [] and phrase2.condition_list!= []:
                            print("wrong")
                        else:
                            phrase1.condition_list = phrase2.condition_list
                    elif "nsubj:" in edge.dep or edge.dep == "nsubj":
                        print("2 branch")
                        for phrase in phrase_list:
                            if phrase.predicate_num == edge.source and phrase.subject_num==-1:
                                phrase.subject_num = edge.target
                                phrase.subject_list.append(edge.target)
                                find_flag = True
                        if find_flag==False:
                            phrase = Phrase(edge.source)
                            phrase.subject_num = edge.target
                            phrase.subject_list.append(edge.target)
                            phrase_list.append(phrase)
                    elif "obj:" in edge.dep or edge.dep == "obj":
                        print("3 branch")
                        for phrase in phrase_list:
                            if phrase.predicate_num == edge.source and phrase.object_num==-1:
                                phrase.object_num = edge.target
                                phrase.object_list.append(edge.target)
                                find_flag = True
                        if find_flag==False:
                            phrase = Phrase(edge.source)
                            phrase.object_num = edge.target
                            phrase.object_list.append(edge.target)
                            phrase_list.append(phrase)
                    elif edge.dep == "obl" or edge.dep == "obl:as":
                        print("4 branch")
                        for phrase in phrase_list:
                            if phrase.predicate_num == edge.source and phrase.object_num==-1:
                                phrase.object_num = edge.target
                                phrase.object_list.append(edge.target)
                                find_flag = True
                        if find_flag==False:
                            phrase = Phrase(edge.source)
                            phrase.object_num = edge.target
                            phrase.object_list.append(edge.target)
                            phrase_list.append(phrase)
                    elif "obl:by" in edge.dep:
                        print("5 branch")
                        for phrase in phrase_list:
                            if phrase.predicate_num == edge.source:
                                phrase.private_condition_num = edge.target
                                phrase.private_condition_list.append(edge.target)
                                find_flag = True
                        if find_flag==False:
                            phrase = Phrase(edge.source)
                            phrase.private_condition_num = edge.target
                            phrase.private_condition_list.append(edge.target)
                            phrase_list.append(phrase)
                    elif ("nmod:" in edge.dep or "obl:" in edge.dep) and ":under" in edge.dep:
                        print("6 branch")
                        for phrase in phrase_list:
                            if phrase.predicate_num == edge.source:
                                phrase.condition_num = edge.target
                                phrase.condition_list.append(edge.target)
                                find_flag = True
                        if find_flag==False:
                            phrase = Phrase(edge.source)
                            phrase.condition_num = edge.target
                            phrase.condition_list.append(edge.target)
                            phrase_list.append(phrase)
                    elif ("nmod:" in edge.dep or "obl:" in edge.dep) and ":in" in edge.dep:
                        print("7 branch")
                        for phrase in phrase_list:
                            if phrase.object_num == edge.source:
                                phrase.private_condition_num = edge.target
                                phrase.private_condition_list.append(edge.target)
                            elif phrase.predicate_num == edge.source:
                                phrase.private_condition_num = edge.target
                                phrase.private_condition_list.append(edge.target)
            
                for edge in dependencies.edge:
                    for phrase in phrase_list:
                        if phrase.predicate_num == edge.source and sentence_text.words[edge.target-1].text == "not":
                            phrase.true_flag = False
                        elif phrase.predicate_num == edge.source :
                            print(sentence_text.words[edge.target-1].text)
                        if phrase.object_num == edge.source and sentence_text.words[edge.target-1].text != "the" and ":in" not in edge.dep:
                            phrase.object_list.append(edge.target)
                        if phrase.subject_num == edge.source and sentence_text.words[edge.target-1].text != "the":
                            phrase.subject_list.append(edge.target)
                        if phrase.condition_num == edge.source and sentence_text.words[edge.target-1].text != "the":
                            phrase.condition_list.append(edge.target)
                        if phrase.private_condition_num == edge.source and sentence_text.words[edge.target-1].text != "the":
                            phrase.private_condition_list.append(edge.target)

                for phrase in phrase_list:
                    subject=""
                    predicate=""
                    object=""
                    condition = ""
                    private_condition = ""
                    if phrase.subject_num!=-1:
                        # print(words[sentence.subject_num-1])
                        phrase.subject_list.sort()
                        for num in phrase.subject_list:
                            subject=subject+sentence_text.words[num-1].text+" "
                        print(subject)
                    if phrase.predicate_num!=-1:
                        # print(words[sentence.predicate_num-1])
                        phrase.predicate_list.sort()
                        for num in phrase.predicate_list:
                            predicate=predicate+sentence_text.words[num-1].text+" "
                        print(predicate)
                        if predicate.endswith("s "):
                            predicate = predicate[0:len(predicate)-2]+" "

                    if phrase.object_num!=-1:
                        # print(words[sentence.object_num-1])
                        phrase.object_list.sort()
                        for num in phrase.object_list:
                            object=object+sentence_text.words[num-1].text+" "
                        print(object)
                    if len(phrase.condition_list)!=0:
                        # print(words[sentence.object_num-1])
                        phrase.condition_list.sort()
                        for num in phrase.condition_list:
                            condition=condition+sentence_text.words[num-1].text+" "
                        condition = condition+", "
                        print("Condition:"+condition)
                    if len(phrase.private_condition_list)!=0:
                        # print(words[sentence.object_num-1])
                        phrase.private_condition_list.sort()
                        for num in phrase.private_condition_list:
                            private_condition=private_condition+sentence_text.words[num-1].text+" "
                        print("Private condition:"+private_condition)
                    print("Phrase:"+subject+predicate+object+"\n")
                    phrase.text = condition+subject+predicate+object+private_condition
                    proposition_num = 0
                    find_flag = False
                    for proposition in  self.proposition_list:
                        if proposition == phrase.text:
                            phrase.proposition_num = proposition_num
                            find_flag = True
                        proposition_num = proposition_num + 1
                    if find_flag==False:
                        self.proposition_list.append(phrase.text)
                        phrase.proposition_num = proposition_num
                    
                self.all_phrase_list=self.all_phrase_list+phrase_list
        return phrase_list      





