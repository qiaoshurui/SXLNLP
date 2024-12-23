# -*- coding: utf-8 -*-
import re
from collections import defaultdict

import torch
from transformers import BertTokenizer

from model import TorchModel

from peft import get_peft_model,LoraConfig

class XPredict():
    def __init__(self,config,model_path):
        self.config = config
        self.model_path = model_path

        model = TorchModel(config)
        # self.model.load_state_dict(torch.load(model_path))

        peft_config = LoraConfig(
            r=8,
            lora_alpha=32,lora_dropout=0.1,
            target_modules=["query", "key", "value"]
        )

        model = get_peft_model(model,peft_config=peft_config)
        state_dict = model.state_dict()

        #更新lora 权重字典
        loaded_weight = torch.load(model_path)
        print(loaded_weight.keys())
        state_dict.update(loaded_weight)

        # 权重更新后重新加载到模型
        model.load_state_dict(state_dict)
        self.model = model

        self.model.eval()
        print("模型加载完毕!")

        self.tokenizer = BertTokenizer.from_pretrained(config["bert_path"])

    def predict(self,sequences):
        for text in sequences:
            input_ids=[]
            input_id = self.tokenizer.encode(text, padding='max_length', max_length=self.config["max_length"], truncation=True)
            # print(x)
            input_ids.append(input_id)
            with torch.no_grad():
                res = self.model(torch.LongTensor(input_ids))
                res = torch.argmax(res, dim=-1)
                print(res)
                labels = res.tolist()[0]
                results_pre = self.decode(text,labels)
                print(results_pre)


    def decode(self, sentence, labels):
        if self.config["model_type"]=='bert':
            labels = labels[1:len(labels) - 1]

        labels = "".join([str(x) for x in labels[:len(sentence)]])
        results = defaultdict(list)
        for location in re.finditer("(04+)", labels):
            s, e = location.span()
            results["LOCATION"].append(sentence[s:e])
        for location in re.finditer("(15+)", labels):
            s, e = location.span()
            results["ORGANIZATION"].append(sentence[s:e])
        for location in re.finditer("(26+)", labels):
            s, e = location.span()
            results["PERSON"].append(sentence[s:e])
        for location in re.finditer("(37+)", labels):
            s, e = location.span()
            results["TIME"].append(sentence[s:e])
        return results


if __name__ == '__main__':
    from config import Config
    xPredict = XPredict(Config,"D:/aiproject/A002/0908/home_work/ner_peft/model_output/epoch_1.pth")
    xPredict.predict([
        "按照波兰检察机关发言人安娜·阿达米亚克的说法，德国相关机构6月向波兰首都华沙的地区检察机关发过“欧洲逮捕令”，涉及德国处理该乌克兰籍嫌疑人所涉案件的相关程序。那名嫌疑人已知最后行踪是7月从乌克兰入境波兰，但波方搜查其住所时并未寻获此人"
    ])


