from transformers import DPRContextEncoder, DPRContextEncoderTokenizer
from transformers import DPRQuestionEncoder, DPRQuestionEncoderTokenizer
import numpy as np
import torch
import tqdm

class DPR:
    def __init__(self, **kwargs):
        # Query tokenizer and model
        self.query_tokenizer = DPRQuestionEncoderTokenizer.from_pretrained('facebook/dpr-question_encoder-single-nq-base')
        self.query_model = DPRQuestionEncoder.from_pretrained('facebook/dpr-question_encoder-single-nq-base')
        self.query_model.cuda()
        self.query_model.eval()
        
        # Context tokenizer and model
        self.context_tokenizer = DPRContextEncoderTokenizer.from_pretrained('facebook/dpr-ctx_encoder-single-nq-base')
        self.context_model = DPRContextEncoder.from_pretrained('facebook/dpr-ctx_encoder-single-nq-base')
        self.context_model.cuda()
        self.context_model.eval()
    
    def encode_queries(self, queries, batch_size=16, **kwargs):
        output = []
        with torch.no_grad():
            for start_idx in tqdm.trange(0, len(queries), batch_size, desc='que'):
                encoded = self.query_tokenizer(queries[start_idx:start_idx+batch_size], truncation=True, padding=True, return_tensors='pt')
                model_out = self.query_model(encoded['input_ids'].cuda(), attention_mask=encoded['attention_mask'].cuda())
                embeddings_q = model_out.pooler_output
                for emb in embeddings_q:
                    output.append(emb)

        out_tensor = torch.stack(output)
        assert out_tensor.shape[0] == len(queries)
        return np.asarray(out_tensor.cpu())
        
    def encode_corpus(self, corpus, batch_size=8, **kwargs):
        
        output = []
        with torch.no_grad():
            for start_idx in tqdm.trange(0, len(corpus), batch_size, desc='pas'):
                titles = [row['title'] for row in corpus[start_idx:start_idx+batch_size]]
                bodies = [row['text']  for row in corpus[start_idx:start_idx+batch_size]]
                encoded = self.context_tokenizer(titles, bodies, truncation='longest_first', padding=True, return_tensors='pt')
                model_out = self.context_model(encoded['input_ids'].cuda(), attention_mask=encoded['attention_mask'].cuda())
                embeddings_q = model_out.pooler_output.detach()
                for emb in embeddings_q:
                    output.append(emb)

        out_tensor = torch.stack(output)
        assert out_tensor.shape[0] == len(corpus)
        return np.asarray(out_tensor.cpu())