from stanfordcorenlp import StanfordCoreNLP
import re

class Phrase(object):

    def __init__(self,predicate_num):
        self.predicate_num = predicate_num
        self.subject_num = -1
        self.condition_num = -1
        self.object_num = -1
        self.property_num = -1
        self.adverb_num = -1
        self.condition_list = []
        self.relation_list = []
        self.predicate_list =[]
        self.predicate_list.append(predicate_num)
        self.subject_list =[]
        self.object_list =[]
        self.adverb_list =[]
        self.text = ""
        self.true_flag = True

class Converter(object):

    def __init__(self):
        self.all_phrase_list:Phrase = []
        self.property_list = []
    
    def text_to_formula(self,long_text):
        formula = ""
        or_lists = long_text.split(" or ")
        for text in or_lists:
            phrases = self.stanza_text_to_ltl(text)
            for phrase in phrases:
                if phrase.true_flag == True:
                    formula = formula+"P"+str(phrase.property_num)+" & "
                else:
                    formula = formula+"!P"+str(phrase.property_num)+" & "
            if len(phrases)>0:
                formula = formula[0:len(formula)-3]+" | "
        if len(or_lists)>0:
            formula = formula[0:len(formula)-3]
        return formula

    def convert_file(self):
        path="define/tiktok/"
        f = open(path+"specifications.txt",'r',encoding='utf-8')
        f_o = open(path+"LTL.txt",'w',encoding='utf-8')
        pattern1 = "(.*)->(.*)if(.*)before(.*), then(.*)"
        lines=f.readlines()
        for line in lines:
            formula = ""
            matchObj = re.match( pattern1, line)
            if matchObj:
                formula = "F!("+self.text_to_formula(matchObj.group(1))+" -> "+self.text_to_formula(matchObj.group(2))+") & F!("+self.text_to_formula(matchObj.group(1).replace(matchObj.group(4),""))+" & "+self.text_to_formula(matchObj.group(3))+" & X("+self.text_to_formula(matchObj.group(1))+") -> X("+self.text_to_formula(matchObj.group(5))+"))"
            elif "->" in line:
                text = line.split("->")
                formula = "F!("+self.text_to_formula(text[0])+" -> "+self.text_to_formula(text[1])+")"
            else:
                formula = self.text_to_formula(line)
            print("Line:"+line)
            print("Formula:"+formula)
            f_o.write("Line:"+line+"\n")
            f_o.write("Formula:"+formula.replace(" ","")+"\n\n")
            f_o.flush()
        property_num = 1
        for property in self.property_list:
            f_o.write("P"+str(property_num)+":"+property+"\n")
            property_num=property_num+1
        f_o.close()
    
    def stanza_text_to_ltl(self,text):
        import stanza
        from stanza.server.ud_enhancer import UniversalEnhancer
        stanza.install_corenlp()
        nlp = stanza.Pipeline('en',
                            processors='tokenize,pos,lemma,depparse')

        with UniversalEnhancer(language="en") as enhancer:
            doc = nlp(text)
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
                print(dependencies.edge)
                for edge in dependencies.edge:
                    find_flag = False
                    phrase1 = None
                    phrase2 = None
                    if "parataxis" in edge.dep or "conj" in edge.dep:
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
                        
                    if "nsubj:" in edge.dep or edge.dep == "nsubj":
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
                        for phrase in phrase_list:
                            if phrase.predicate_num == edge.source:
                                phrase.adverb_num = edge.target
                                phrase.adverb_list.append(edge.target)
                                find_flag = True
                        if find_flag==False:
                            phrase = Phrase(edge.source)
                            phrase.adverb_num = edge.target
                            phrase.adverb_list.append(edge.target)
                            phrase_list.append(phrase)
                    elif "obl:" in edge.dep:
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
                    
            
                for edge in dependencies.edge:
                    for phrase in phrase_list:
                        if phrase.predicate_num == edge.source and sentence_text.words[edge.target-1].text == "not":
                            phrase.true_flag = False
                        elif phrase.predicate_num == edge.source :
                            print(sentence_text.words[edge.target-1].text)
                        if phrase.object_num == edge.source and sentence_text.words[edge.target-1].text != "the":
                            phrase.object_list.append(edge.target)
                        if phrase.subject_num == edge.source and sentence_text.words[edge.target-1].text != "the":
                            phrase.subject_list.append(edge.target)
                        if phrase.condition_num == edge.source and sentence_text.words[edge.target-1].text != "the":
                            phrase.condition_list.append(edge.target)
                        if phrase.adverb_num == edge.source and sentence_text.words[edge.target-1].text != "the":
                            phrase.adverb_list.append(edge.target)

                for phrase in phrase_list:
                    subject=""
                    predicate=""
                    object=""
                    condition = ""
                    adverb = ""
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
                        if predicate.endswith("es "):
                            predicate = predicate[0:len(predicate)-3]+" "
                        elif predicate.endswith("s "):
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
                    if len(phrase.adverb_list)!=0:
                        # print(words[sentence.object_num-1])
                        phrase.adverb_list.sort()
                        for num in phrase.adverb_list:
                            adverb=adverb+sentence_text.words[num-1].text+" "
                        print("Adverb:"+adverb)
                    print("Phrase:"+subject+predicate+object+"\n")
                    phrase.text = condition+subject+predicate+object+adverb
                    property_num = 1
                    find_flag = False
                    for property in  self.property_list:
                        if property == phrase.text:
                            phrase.property_num = property_num
                            find_flag = True
                        property_num = property_num + 1
                    if find_flag==False:
                        self.property_list.append(phrase.text)
                        phrase.property_num = property_num
                    
                self.all_phrase_list=self.all_phrase_list+phrase_list
        return phrase_list      

converter = Converter()
converter.convert_file()



