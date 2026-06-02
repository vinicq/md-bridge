---
title: "arxiv-2207.09238-formal-algorithms-transformers"
date: "2022-07-20"
source: "arxiv-2207.09238-formal-algorithms-transformers.pdf"
pages: 16
---

*19 July 2022*

# Formal Algorithms for Transformers

**Mary Phuong**^1^ **^and Marcus Hutter^**^1^

1DeepMind

**This document aims to be a self-contained, mathematically precise overview of transformer architec-** **tures and algorithms (*****not*** **results). It covers what transformers are, how they are trained, what they are** **used for, their key architectural components, and a preview of the most prominent models. The reader** **is assumed to be familiar with basic ML terminology and simpler neural network architectures such as** **MLPs.**

*Keywords: formal algorithms, pseudocode, transformers, attention, encoder, decoder, BERT, GPT, Gopher,* *tokenization, training, inference.*

## arXiv:2207.09238v1  \[cs.LG\]  19 Jul 2022

plete, precise and compact overview of trans- former architectures and formal algorithms (but *not* results). It covers what Transformers are (Sec- tion 6), how they are trained (Section 7), what they’re used for (Section 3), their key architec- tural components (Section 5), tokenization (Sec- tion 4), and a preview of practical considerations (Section 8) and the most prominent models.

### Contents

**1** **Introduction** [**1**](#page-1) **2** **Motivation** [**1**](#page-1) **3** **Transformers and Typical Tasks** [**3**](#page-3) **4** **Tokenization: How Text is Represented** [**4**](#page-4) **5** **Architectural Components** [**4**](#page-4) **6** **Transformer Architectures** [**7**](#page-7) **7** **Transformer Training and Inference** [**8**](#page-8) **8** **Practical Considerations** [**9**](#page-9) **A** **References** [**9**](#page-9) **B** **List of Notation** [**16**](#page-16)

The essentially complete pseudocode is about 50 lines, compared to thousands of lines of ac- tual real source code. We believe these formal algorithms will be useful for theoreticians who require compact, complete, and precise formu- lations, experimental researchers interested in implementing a Transformer from scratch, and encourage authors to augment their paper or text book with formal Transformer algorithms (Sec- tion 2).

*A famous colleague once sent an actually very* *well-written paper he was quite proud of to a fa-* *mous complexity theorist. His answer: “I can’t ﬁnd* *a theorem in the paper. I have no idea what this* *paper is about.”*

**1. Introduction**

    The reader is assumed to be familiar with ba- sic ML terminology and simpler neural network architectures such as MLPs.

Transformers are deep feed-forward artiﬁcial neu- ral networks with a (self)attention mechanism. They have been tremendously successful in natu- ral language processing tasks and other domains. Since their inception 5 years ago \[VSP+17\], many variants have been suggested \[LWLQ21\]. Descrip- tions are usually graphical, verbal, partial, or in- cremental. Despite their popularity, it seems no pseudocode has ever been published for any vari- ant. Contrast this to other ﬁelds of computer science, even to “cousin” discipline reinforcement learning \[MKS+13, SBB18, EMK+21\].

In short, a (formally inclined) reader, upon un- derstanding the contents of this document, will have a solid grasp of transformers: they will be ready to read and contribute to the literature on the topic as well as implement their own Trans- former using the pseudocode as templates.

          **2. Motivation**

The true story above the introduction describes quite well the feeling we have when browsing

This report intends to rectify the situation for Transformers. It aims to be a self-contained, com*Corresponding author(s):* {*buiphuong,mhutter*}*@deepmind.com* © 2022 DeepMind. All rights reserved

Formal Algorithms for Transformers authors writing the diﬀerent sections. The core algorithms for the models should be accompa- nied by the wrapper algorithms that call them, e.g. (pre)training, ﬁne-tuning, prompting, infer- ence, deployment. Sometimes this is simple, but sometimes the magic happens there. In any case, if these things are not formally stated they re- main unclear. Again, if the setup is standard and has been formally explained elsewhere, a simple reference will do.

many Deep Learning (DL) papers; unable to ﬁg- ure out the algorithmic suggestions exactly. For practitioners, the papers may be suﬃciently de- tailed, but the precision needed by theoreticians is usually higher. For reasons not entirely clear to us, the DL community seems shy of providing pseudocode for their neural network models. Be- low we describe the SOTA in DL paper writing and argue for the value of formal algorithms. The reader already convinced about their merit can without loss skip this section.

**Source code vs pseudocode.** Providing open source code is very useful, but not a proper sub- stitute for formal algorithms. There is a massive diﬀerence between a (partial) Python dump and well-crafted pseudocode. A lot of abstraction and clean-up is necessary: remove boiler plate code, use mostly single-letter variable names, replace code by math expressions wherever possible, e.g. replace loops by sums, remove (some) optimiza- tions, etc. A well-crafted pseudocode is often less than a page and still essentially complete, com- pared to often thousands of lines of real source code. This is hard work no-one seems to be will- ing to do. Of course a forward process of ﬁrst designing algorithms and write up pseudocode on paper, and then implementing it is ﬁne too, but few DL practitioners seem to work that way.

**The lack of scientiﬁc precision and detail in DL** **publications.** Deep Learning has been tremen- dously successful in the last 5 to 10 years with thousands of papers published every year. Many describe only informally how they change a pre- vious model, Some 100+ page papers contain only a few lines of prose informally describing the model \[RBC+21\]. At best there are some high-level diagrams. No pseudocode. No equa- tions. No reference to a precise explanation of the model. One may argue that most DL models are minor variations of a few core architectures, such as the Transformer \[VSP+17\], so a reference aug- mented by a description of the changes should suﬃce. This would be true if (a) the changes were described precisely, (b) the reference architecture has been described precisely elsewhere, and (c) a reference is given to this description. Some if not all three are lacking in most DL papers. To the best of our knowledge no-one has even provided pseudocode for the famous Transformer and its encoder/decoder-only variations.

**Examples** **of** **good** **neural** **network** **pseu-** **docode and mathematics and explanations.** Multi-Layer Perceptrons (MLPs) are usually well- described in many papers, e.g. \[MPCB14, BFT17, JGH18\], though also without pseudocode. For a rare text-book example of pseudocode for a non- trivial neural network architecture, see Algorithm S2 of \[SGBK+21\], which constitutes a *complete*, i.e. *essentially executable*, pseudocode of just 25 lines based on a 350-line Python Colab toy im- plementation, which itself is based on a proper 1000+ line implementation.

**Interfacing algorithms.** Equally important are proper explanations of how these networks are trained and used, but sometimes it is not even clear what the inputs and outputs and potential side-eﬀects of the described model are. Of course someone experienced would usually be able to correctly guess, but this is not a particularly sci- entiﬁc approach. The experimental section in publications often does not explain what is ac- tually fed into the algorithms and how. If there is some explanation in the methods section, it is often disconnected from what is described in the experimental section, possibly due to diﬀerent

This work aims to do the same for Transform- ers: The whole decoder-only Transformer GPT Algorithm 10 based on attention Algorithms 4 and 5 and normalization Algorithm 6 including training Algorithm 13 and prompting and infer- ence Algorithm 14 all-together is less than 50 lines of pseudocode, compared to e.g. the 2000-

2

Formal Algorithms for Transformers

          **3. Transformers and Typical Tasks**

line self-contained C-implementation \[Bel21\].

\[Ala19\] is a great blog-post explaining Trans- formers and \[EGKZ21\] describes the attention mechanism to suﬃcient mathematical precision to allow proving properties about it, but neither provides pseudocode. \[Elh21\] is an attempt to understand Transformers by reverse-engineering the computations they perform and interpreting them as circuits.

Transformers are neural network models that ex- cel at natural language processing, or more gen- erally at modelling sequential data. Two common types of tasks they are used for are *sequence mod-* *elling* and *sequence-to-sequence prediction*.

**Notation.** Let *𝑉*denote a ﬁnite set, called a *vo-* *cabulary*, often identiﬁed with \[*𝑁*V\] := {1*, ..., 𝑁*V}. This could be words or letters, but typically are sub-words, called tokens. Let *𝒙*≡*𝑥*\[1 : *ℓ*\] ≡ *𝑥*\[1\]*𝑥*\[2\]*...𝑥*\[*ℓ*\] ∈*𝑉*^∗be a sequence of tokens, e.g.^ a sentence or a paragraph or a document. Un- like in Python, we use arrays starting from 1, and *𝑥*\[1 : *ℓ*\] includes *𝑥*\[*ℓ*\]. For a matrix *𝑀*∈ℝ*^𝑑^*^×^*^𝑑^*^′, we^ write *𝑀*\[*𝑖,* :\] ∈ℝ*^𝑑^*^′ for the^ *𝑖*th row and *𝑀*\[:*, 𝑗*\] ∈ℝ*^𝑑^*

**Motivation.** But does anyone actually need pseudocode and what would they be useful for (we sometimes get asked)? We ﬁnd the absence of pseudocode in DL and this question quite perplex- ing, but apparently it requires answering. Pro- viding such pseudocode can be useful for many purposes:

for the *𝑗*-th column. We use matrix × column vec- tor convention more common in mathematics, compared to the default row vector × matrix in the transformer literature, i.e. our matrices are transposed. See Appendix B for a complete list of notation.

- They can be used as templates and adapted to precisely describe future variations, and therewith set a new standard in DL publish- ing. We explicitly encourage the reader to copy and adapt them to their needs and cite the original as “adapted from \[PH22\]”. • Having all that matters on one page in front of you makes it easier to develop new varia- tions compared to reading prose or scrolling through 1000s of lines of actual code. • They can be used as a basis for new imple- mentations from scratch, e.g. in diﬀerent programming languages, without having to wade through and reverse-engineer existing idiosyncratic real source code. • They may establish notational convention, which eases communication and reading fu- ture variations. • The process of converting source code into pseudocode can exhibit implementation er- rors (as it e.g. did in \[SGBK+21\]). • Theoreticians need compact, complete, and precise representations for reasoning and ul- timately proving properties about algorithms. They are often unwilling or unable to re- verse engineer code, or guess the meaning of words or fancy diagrams.

    **Chunking.** The predominant paradigm in ma- chine learning is (still) learning from independent and identically distributed (i.i.d.) data. Even for sequence modelling for practical reasons this tra- dition is upheld. The training data may natu- rally be a collection of (independent) articles, but even then, some may exceed the maximal context length *ℓ*max transformers can handle. In this case, an article is crudely broken into shorter chunks of length ≤*ℓ*max.

    **Sequence modelling (DTransformer).** Given a vocabulary *𝑉*, let *𝒙𝑛*∈*𝑉*^∗for^ *𝑛*∈\[*𝑁*data\] be a dataset of sequences (imagined to be) sampled i.i.d. from some distribution *𝑃*over *𝑉*^∗. The goal^ is to learn an estimate ˆ*𝑃*of the distribution *𝑃*(*𝒙*). In practice, the distribution estimate is often de- composed via the chain rule as ˆ*𝑃*(*𝒙*) = ˆ*𝑃𝜽*(*𝑥*\[1\]) · ˆ*𝑃𝜽*(*𝑥*\[2\] | *𝑥*\[1\]) · · · ˆ*𝑃𝜽*(*𝑥*\[*ℓ*\] | *𝒙*\[1 : *ℓ*−1\]), where *𝜽* consists of all neural network parameters to be learned. The goal is to learn a distribution over a single token *𝑥*\[*𝑡*\] given its preceding tokens *𝑥*\[1 : *𝑡*−1\] as context.

With this motivation in mind, the following ﬁve sections formally describe all aspects of trans- former architectures, training, and inference.

3

Formal Algorithms for Transformers

(plus punctuation). In the example above, we’d get a sequence of length 7: \[‘My ’, ‘grandma ’, ‘makes ’, ...\]. Word-level tokenization tends to require a very large vocabulary and cannot deal with new words at test time.

Examples include e.g. language modelling, RL policy distillation, or music generation.

**Sequence-to-sequence (seq2seq) prediction** **(EDTransformer).** Given a vocabulary *𝑉*and an i.i.d. dataset of sequence pairs (*𝒛𝑛, 𝒙𝑛*) ∼*𝑃*, where *𝑃*is a distribution over *𝑉*^∗×^ *𝑉*^∗, learn an^ estimate of the conditional distribution *𝑃*(*𝒙*|*𝒛*). In practice, the conditional distribution estimate is often decomposed as ˆ*𝑃*(*𝒙*|*𝒛*) = ˆ*𝑃𝜽*(*𝑥*\[1\] | *𝒛*) · ˆ*𝑃𝜽*(*𝑥*\[2\] | *𝑥*\[1\]*, 𝒛*) · · · ˆ*𝑃𝜽*(*𝑥*\[*ℓ*\] | *𝒙*\[1 : *ℓ*−1\]*, 𝒛*).

**Subword tokenization.** This is the method used in practice nowadays: *𝑉*is a set of com- monly occurring word segments like ‘cious’, ‘ing’, ‘pre’. Common words like ‘is ’ are often a separate token, and single characters are also included in *𝑉*to ensure all words are expressible.

Examples include translation (*𝒛*= a sentence in English, *𝒙*= the same sentence in German), question answering (*𝒛*= question, *𝒙*= the corre- sponding answer), text-to-speech (*𝒛*= a piece of text, *𝒙*= a voice recording of someone reading the text).

There are in fact many ways to do subword to- kenization. One of the simplest and most success- ful ones is Byte Pair Encoding \[Gag94, SHB16\] used in GPT-2 \[RWC+19\].

**Final vocabulary and text representation.** Given a choice of tokenization / vocabulary, each vocabulary element is assigned a unique index in {1*,* 2*, . . . , 𝑁*V −3}. A number of special tokens are then added to the vocabulary. The number of special tokens varies, and here we will con- sider three: `mask_token` := *𝑁*V −2, used in masked language modelling (see Algorithm 12); `bos_token` := *𝑁*V −1, used for representing the beginning of sequence; and `eos_token` := *𝑁*V, used for representing the end of sequence. The complete vocabulary has *𝑁*V = |*𝑉*| elements.

**Classiﬁcation (ETransformer).** Given a vocab- ulary *𝑉*and a set of classes \[*𝑁*C\], let (*𝒙𝑛, 𝑐𝑛*) ∈ *𝑉*^∗× \[^*𝑁*C\] for *𝑛*∈\[*𝑁*data\] be an i.i.d. dataset of sequence-class pairs sampled from *𝑃*(*𝒙, 𝑐*). The goal in classiﬁcation is to learn an estimate of the conditional distribution *𝑃*(*𝑐*|*𝒙*).

Examples include e.g. sentiment classiﬁcation, spam ﬁltering, toxicity classiﬁcation.

**4. Tokenization: How Text is Repre-** **sented**

    A piece of text is represented as a sequence of indices (called *token IDs*) corresponding to its (sub)words, preceded by `bos_token` and fol- lowed by `eos_token`.

In the context of natural language tasks, *tok-* *enization* refers to how a piece of text such as “My grandma makes the best apple pie.” is rep- resented as a sequence of vocabulary elements (called *tokens*).

          **5. Architectural Components**

The following are the neural network build- ing blocks (functions with learnable parameters) from which transformers are made. Full archi- tectures featuring these building blocks are pre- sented in the next section. (By a slight abuse of no- tation, we identify *𝑉*with the set {1*,* 2*, . . . , 𝑁*V}.)

**Character-level tokenization.** One possible choice is to let *𝑉*be the English alphabet (plus punctuation). In the example above, we’d get a sequence of length 36: \[‘M’, ‘y’, ‘ ’, ...\]. Character- level tokenization tends to yield very long se- quences.

**Token** **embedding.** The token embedding learns to represent each vocabulary element as a vector in ℝ*^𝑑^*^e; see Algorithm 1.^

**Word-level** **tokenization.** Another choice would be to let *𝑉*consist of all English words

4

Formal Algorithms for Transformers

**Algorithm 1:** Token embedding.

**Algorithm 2:** Positional embedding.

**Input:** *𝑣*∈*𝑉* \[*𝑁*V\], a token ID. **Output:** *𝒆*∈ℝ*^𝑑^*^e, the vector representation^ of the token. **Parameters:** *𝑾𝒆*∈ℝ*^𝑑^*^e×^*^𝑁^*^V, the token^ embedding matrix.

**Input:** *ℓ*∈\[*ℓ*max\], position of a token in the sequence. **Output:** *𝒆𝒑*∈ℝ*^𝑑^*^e, the vector^ representation of the position. **Parameters:** *𝑾𝒑*∈ℝ*^𝑑^*^e×^*^ℓ^*^max, the positional^ embedding matrix.

### 1 return 𝒆= 𝑾𝒆\[:, 𝑣\]

### 1 return 𝒆𝒑= 𝑾𝒑\[:, ℓ\]

**Positional embedding.** The positional embed- ding learns to represent a token’s position in a sequence as a vector in ℝ*^𝑑^*^e. For example, the posi-^ tion of the ﬁrst token in a sequence is represented by a (learned) vector *𝑾𝒑*\[:*,* 1\], the position of the second token is represented by another (learned) vector *𝑾𝒑*\[:*,* 2\], etc. The purpose of the positional embedding is to allow a Transformer to make sense of word ordering; in its absence the rep- resentation would be permutation invariant and the model would perceive sequences as “bags of words” instead.

network to make use of contextual information (e.g. preceding text or the surrounding text) for predicting the current token.

On a high level, attention works as follows: the token currently being predicted is mapped to a *query* vector *𝒒*∈ℝ*^𝑑^*^attn, and the tokens in the^ context are mapped to *key* vectors *𝒌𝑡*∈ℝ*^𝑑^*^attn and^ *value* vectors *𝒗𝑡*∈ℝ*^𝑑^*^value. The inner products^ *𝒒*^⊺^*𝒌𝑡* are interpreted as the degree to which token *𝑡*∈*𝑉* is important for predicting the current token *𝑞* – they are used to derive a distribution over the context tokens, which is then used to combine the value vectors. An intuitive explanation how this achieves attention can be found at \[Ala18, Ala19\]. The precise algorithm is given in Algorithm 3.

Learned positional embeddings require that in- put sequence length is at most some ﬁxed number *ℓ*max (the size of the learned positional embedding matrix must be ﬁnite and ﬁxed in advance of train- ing). An intuitive explanation of how this works can be found at \[Ala18\]. For pseudocode, see Algorithm 2.

**Algorithm 3:** Basic single-query attention.

**Input:** *𝒆*∈ℝ*^𝑑^*^in, vector representation of^ the current token **Input:** *𝒆𝑡*∈ℝ*^𝑑^*^in, vector representations of^ context tokens *𝑡*∈\[*𝑇*\]. **Output: ˜***𝒗*∈ℝ*^𝑑^*^out, vector representation of^ the token and context combined. **Parameters:** *𝑾𝒒, 𝑾𝒌*∈ℝ*^𝑑^*^attn×^*^𝑑^*^in,^ *𝒃𝒒, 𝒃𝒌*∈ℝ*^𝑑^*^attn, the query and^ key linear projections. **Parameters:** *𝑾𝒗*∈ℝ*^𝑑^*^out×^*^𝑑^*^in,^ *𝒃𝒗*∈ℝ*^𝑑^*^out, the^ value linear projection.

Not all transformers make use of *learned* posi- tional embeddings, some use a hard-coded map- ping *𝑾𝒑*: ℕ→ℝ*^𝑑^*^e instead \[Ker21\]. Such hard-^ coded positional embeddings can (theoretically) handle arbitrarily long sequences. The original Transformer \[VSP+17\] uses

*𝑾𝒑*\[2*𝑖*−1*, 𝑡*\] = sin(*𝑡*/*ℓ*^2^*^𝑖^*^/^*^𝑑^*^e^ max )*^,^*

*𝑾𝒑*\[2*𝑖, 𝑡*\] = cos(*𝑡*/*ℓ*^2^*^𝑖^*^/^*^𝑑^*^e^ max )*^.^* for 0 *< 𝑖*≤*𝑑*e/2.

**1** *𝒒*←*𝑾𝒒𝒆*+ *𝒃𝒒* **2** ∀*𝑡*: *𝒌𝑡*←*𝑾𝒌𝒆𝑡*+ *𝒃𝒌* **3** ∀*𝑡*: *𝒗𝑡*←*𝑾𝒗𝒆𝑡*+ *𝒃𝒗*

The positional embedding of a token is usu- ally added to the token embedding to form a token’s initial embedding. For the *𝑡*-th token of a sequence *𝒙*, the embedding is

**4** ∀*𝑡*: *𝛼𝑡*= exp(*𝒒*^⊺^*𝒌𝑡*/√

*𝑑*attn) Í *𝑢*^exp(^*^𝒒^*^⊺^*^𝒌𝑢^*^/√^

*𝑑*attn)

### 5 return ˜𝒗= Í^𝑇^ 𝑡=1 𝛼𝑡𝒗𝑡

### 𝒆= 𝑾𝒆\[:, 𝑥\[𝑡\]\] + 𝑾𝒑\[:, 𝑡\]. (1)

There are many ways the basic attention mech- anism is used in transformers. We list some of the most common variants below.

**Attention.** Attention is the main architectural component of transformers. It enables a neural

5

Formal Algorithms for Transformers on *𝑿*\[:*,* 1 : *𝑡*\], hence can be used to predict *𝑿*\[:*, 𝑡*+ 1\].

It will be useful to deﬁne the softmax function for matrix arguments, as well as a Mask matrix:

softmax(*𝑨*)\[*𝑡*z*, 𝑡*x\] := exp *𝐴*\[*𝑡*z*, 𝑡*x\] Í *𝑡*^exp^ *^𝐴^*^\[^*^𝑡, 𝑡^*x\] *^,^* (2)

**Cross-attention.** Given two sequences of to- ken representations (often in the context of a sequence-to-sequence task), this variant applies attention to each token of the primary token se- quence *𝑿*, treating the second token sequence *𝒁*as the context. See Algorithm 4, called with Mask≡1. While the output **˜***𝑽*and input sequences *𝑿*have the same length *ℓ*x, the context sequence *𝒁*can have diﬀerent length *ℓ*z.

Mask\[*𝑡*z*, 𝑡*x\] =  1 for bidirectional attention \[\[*𝑡*z ≤*𝑡*x\]\] for unidirectional att. (3)

### Algorithm 4: ˜𝑽←`Attention`(𝑿, 𝒁|W𝒒𝒌𝒗, Mask)

`/* Computes a single (masked) self- or` `cross- attention head.` `*/` **Input:** *𝑿*∈ℝ*^𝑑^*^x×^*^ℓ^*^x^*, 𝒁*∈ℝ*^𝑑^*^z×^*^ℓ^*^z, vector^ representations of primary and context sequence. **Output: ˜***𝑽*∈ℝ*^𝑑^*^out×^*^ℓ^*^x, updated^ representations of tokens in *𝑿*, folding in information from tokens in *𝒁*. **Parameters: W***𝒒𝒌𝒗*consisting of: *𝑾𝒒*∈ℝ*^𝑑^*^attn×^*^𝑑^*^x,^ *𝒃𝒒*∈ℝ*^𝑑^*^attn^

**Multi-head attention.** The attention algorithm presented so far (Algorithm 4) describes the op- eration of a single *attention head*. In practice, transformers run multiple attention heads (with separate learnable parameters) in parallel and combine their outputs; this is called *multi-head* *attention*; see Algorithm 5

*𝑾𝒌*∈ℝ*^𝑑^*^attn×^*^𝑑^*^z,^ *𝒃𝒌*∈ℝ*^𝑑^*^attn^

*𝑾𝒗*∈ℝ*^𝑑^*^out×^*^𝑑^*^z,^ *𝒃𝒗*∈ℝ*^𝑑^*^out.^ **Hyperparameters:** Mask∈{0*,*1}*^ℓ^*^z×^*^ℓ^*^x, ↑(3)^

**1** *𝑸*←*𝑾𝒒𝑿*+ *𝒃𝒒***1**^⊺^ \[\[*𝑸*uery ∈ℝ*^𝑑^*^attn×^*^ℓ^*^x\]\]^

### Algorithm 5: ˜𝑽←`MHAttention`(𝑿, 𝒁|W, Mask)

**2** *𝑲*←*𝑾𝒌𝒁*+ *𝒃𝒌***1**^⊺^ \[\[*𝑲*ey ∈ℝ*^𝑑^*^attn×^*^ℓ^*^z\]\]^

`/* Computes Multi-Head (masked) self-` `or cross- attention layer.` `*/` **Input:** *𝑿*∈ℝ*^𝑑^*^x×^*^ℓ^*^x^*, 𝒁*∈ℝ*^𝑑^*^z×^*^ℓ^*^z, vector^ representations of primary and context sequence. **Output: ˜***𝑽*∈ℝ*^𝑑^*^out×^*^ℓ^*^x, updated^ representations of tokens in *𝑿*, folding in information from tokens in *𝒁*. **Hyperparameters:** *𝐻*, number of attention heads **Hyperparameters:** Mask∈{0*,*1}*^ℓ^*^z×^*^ℓ^*^x, ↑(3)^ **Parameters: W** consisting of For *ℎ*∈\[*𝐻*\], **W***^ℎ^* *𝒒𝒌𝒗*^consisting of:^ | *𝑾ℎ* *𝒒*^∈ℝ^*^𝑑^*^attn×^*^𝑑^*^x,^ *^𝒃ℎ^* *𝒒*^∈ℝ^*^𝑑^*^attn,^ | *𝑾ℎ* *𝒌*^∈ℝ^*^𝑑^*^attn×^*^𝑑^*^z,^ *^𝒃ℎ^* *𝒌*^∈ℝ^*^𝑑^*^attn,^ | *𝑾ℎ* *𝒗*^∈ℝ^*^𝑑^*^mid×^*^𝑑^*^z,^ *^𝒃ℎ^* *𝒗*^∈ℝ^*^𝑑^*^mid.^ *𝑾𝒐*∈ℝ*^𝑑^*^out×^*^𝐻𝑑^*^mid,^ *𝒃𝒐*∈ℝ*^𝑑^*^out.^

**3** *𝑽*←*𝑾𝒗𝒁*+ *𝒃𝒗***1**^⊺^ \[\[*𝑽*alue ∈ℝ*^𝑑^*^out×^*^ℓ^*^z\]\]^

**4** *𝑺*←*𝑲*^⊺^*𝑸* \[\[*𝑺*core ∈ℝ*^ℓ^*^z×^*^ℓ^*^x\]\]^

**5** ∀*𝑡*z*, 𝑡*x*,* if ¬Mask\[*𝑡*z*, 𝑡*x\] then *𝑆*\[*𝑡*z*, 𝑡*x\] ←−∞

### 6 return ˜𝑽= 𝑽· softmax   𝑺/√

*𝑑*attn 

**Bidirectional** **/** **unmasked** **self-attention.** Given a sequence of token representations, this variant applies attention to each token, treating all tokens in the sequence as the context. See Algorithm 4, called with token sequence *𝒁*= *𝑿* and no masking (Mask≡1).

**Unidirectional** **/** **masked** **self-attention.** Given a sequence of token representations, this variant applies attention to each token, treating all preceding tokens (including itself) as the con- text. Future tokens are masked out, so this causal auto-regressive version can be used for online prediction. See Algorithm 4, called with token sequence *𝒁*= *𝑿*and Mask\[*𝑡*z*, 𝑡*x\] := \[\[*𝑡*z ≤*𝑡*x\]\]. For this Mask, the output **˜***𝑽*\[:*,* 1 : *𝑡*\] only depends

**1** For *ℎ*∈\[*𝐻*\]:

**2** *𝒀ℎ*←`Attention`(*𝑿, 𝒁*|**W***^ℎ^* *𝒒𝒌𝒗,* ^Mask)^

**3** *𝒀*←\[*𝒀*^1;^*𝒀*^2;^ *. . .* ;*𝒀𝐻*\]

### 4 return ˜𝑽= 𝑾𝒐𝒀+ 𝒃𝒐1^⊺^

6

Formal Algorithms for Transformers

Algorithms 8, 11 and 15. • BERT \[DCLT19\], which is an instance of an encoder-only transformer (encoder-only means that it is derived from the encoder- decoder architecture by dropping the de- coder part), Algorithms 9 and 12. • GPT \[RWC+19, BMR+20\], which is an in- stance of a decoder-only transformer, Algo- rithms 10, 13 and 14.

### Algorithm 6: ˆ𝒆←`layer_norm`(𝒆|𝜸, 𝜷)

`/* Normalizes layer activations` *𝒆*`.` `*/` **Input:** *𝒆*∈ℝ*^𝑑^*^e, neural network activations.^ **Output:** b*𝒆*∈ℝ*^𝑑^*^e, normalized activations.^ **Parameters:** *𝜸, 𝜷*∈ℝ*^𝑑^*^e, element-wise^ scale and oﬀset.

**1** *𝒎*←Í*^𝑑^*^e^ *𝑖*=1 *𝒆*^\[^*^𝑖^*^\]/^*^𝑑^*^e^

### 2 𝑣←Í^𝑑^^e^ 𝑖=1(^𝒆^^\[^^𝑖^^\] −^^𝒎^^)2/^^𝑑^^e^

**3 return** b*𝒆*= *𝒆*^−^*^𝒎^* √*𝑣*⊙*𝜸*+ *𝜷*, where ⊙denotes element-wise multiplication.

While the main architectural diﬀerence between BERT and GPT is in attention masking, they also diﬀer in a number of less important ways: e.g. they use diﬀerent activation functions and the layer-norms are positioned diﬀerently. We in- cluded these diﬀerences in the pseudocode to stay faithful to the original algorithms, but note that diﬀerent transformer architectures may adopt these selectively.

**Algorithm 7:** Unembedding.

**Input:** *𝒆*∈ℝ*^𝑑^*^e, a token encoding.^ **Output:** *𝒑*∈Δ(*𝑉*), a probability distribution over the vocabulary. **Parameters:** *𝑾𝒖*∈ℝ*^𝑁^*^V×^*^𝑑^*^e, the^ unembedding matrix.

### 1 return 𝒑= softmax(𝑾𝒖𝒆)

To simplify notation, we denote by **W** the en- tire set of parameters (query, key, value and out- put linear projections) required by a multi-head attention layer:

**Layer normalisation.** Layer normalisation ex- plicitly controls the mean and variance of individ- ual neural network activations; the pseudocode is given in Algorithm 6. Some transformers use a simpler and more computationally eﬃcient ver- sion of layer normalization setting *𝒎*= *𝜷*= 0, called root mean square layer normalisation, or RMSnorm.

*𝑾ℎ* *𝒒*^∈ℝ^*^𝑑^*^attn×^*^𝑑^*^x^*^,^* *𝒃ℎ* *𝒒*^∈ℝ^*^𝑑^*^attn^*^,^* *ℎ*∈\[*𝐻*\] *𝑾ℎ* *𝒌*^∈ℝ^*^𝑑^*^attn×^*^𝑑^*^z^*^,^* *𝒃ℎ* *𝒌*^∈ℝ^*^𝑑^*^attn^*^,^* *ℎ*∈\[*𝐻*\] *𝑾ℎ* *𝒗*^∈ℝ^*^𝑑^*^mid×^*^𝑑^*^z^*^,^* *𝒃ℎ* *𝒗*^∈ℝ^*^𝑑^*^mid^*^,^* *ℎ*∈\[*𝐻*\] *𝑾𝒐*∈ℝ*^𝑑^*^out×^*^𝐻𝑑^*^mid^*,* *𝒃𝒐*∈ℝ*^𝑑^*^out^

**W** := ©­­­ « ª®®® ¬ (4)

**Unembedding.** The unembedding learns to convert a vector representation of a token and its context into a distribution over the vocabulary elements; see Algorithm 7. The algorithm de- scribes an independently learned unembedding matrix, but note that sometimes the unembed- ding matrix is instead ﬁxed to be the transpose of the embedding matrix.

**Encoder-decoder** **/** **sequence-to-sequence** **transformer \[VSP**[^+^](#page-10)**17\].** This is the very ﬁrst transformer. It was originally used for sequence- to-sequence tasks (machine translation), which is why it is more complicated than its successors.

The idea behind the architecture is as follows: First, the context sequence is encoded using bidi- rectional multi-head attention. The output of this ‘encoder’ part of the network is a vector represen- tation of each context token, taking into account the entire context sequence. Second, the primary sequence is encoded. Each token in the primary sequence is allowed to use information from the encoded context sequence, as well as primary se- quence tokens that precede it. See Algorithm 8 for more details.

**6. Transformer Architectures**

This section presents a few prominent transformer architectures, based on attention Algorithms 4 and 5 and using normalization Algorithm 6, in roughly historical order:

- EDT \[VSP+17\] The original sequence-to- sequence / Encoder-Decoder Transformer,

7

Formal Algorithms for Transformers

**Encoder-only transformer:** **BERT \[DCLT19\].** BERT is a bidirectional transformer trained on the task of masked language modelling. Given a piece of text with some tokens masked out, the goal is to correctly recover the masked-out tokens. The original use of BERT was to learn generally useful text representations, which could then be adapted for various downstream NLP tasks. The masking is not performed via the Mask parameter but diﬀerently: During training each input token is replaced with probability *𝑝*mask by a dummy to- ken `mask_token`, and evaluation is based on the reconstruction probability of these knocked-out tokens (see Algorithm 12).

**Multi-domain** **decoder-only** **transformer:** **Gato \[RZP**[^+^](#page-10)**22\].** Gato is a multi-modal multi- task transformer built by DeepMind. It is a single neural network that can play Atari, navigate 3D environments, control a robotic arm, caption images, have conversations, and more.

Under the hood, each modality is converted into a sequence prediction problem by a sepa- rate tokenization and embedding method; for example images are divided into non-overlapping 16 × 16 patches, ordered in raster order (left-to- right, top-to-bottom) and processed by a ResNet block to obtain a vector representation.

The actual Gato architecture is then a decoder- only transformer like the one in Algorithm 10, but where Line 2 is replaced with modality-speciﬁc embedding code.

The BERT architecture resembles the encoder part of the seq2seq transformer (hence ‘encoder- only’). It is described in detail in Algorithm 9. It uses the GELU nonlinearity instead of ReLU:

          **7. Transformer Training and Infer-** **ence**

### GELU(𝑥) = 𝑥· ℙ𝑋∼N(0,1) \[𝑋< 𝑥\]. (5)

(When called with vector or matrix arguments, GELU is applied element-wise.)

This section lists the pseudocode for various algo- rithms for training and using transformers:

          - **EDTraining()** Algorithm 11 shows how to train a sequence-to-sequence transformer (the original Transformer \[VSP+17\]). • **ETraining()** Algorithm 12 shows how to train a transformer on the task of masked language modelling (like BERT \[DCLT19\]). • **DTraining()** Algorithm 13 shows how to train a transformer on the task of next to- ken prediction (like CPT-x \[BMR+20\] and Gopher \[RBC+21\]). • **DInference()** Algorithm 14 shows how to prompt a transformer trained on next token prediction (like GPT-x \[BMR+20\]). The tem- perature parameter *𝜏*interpolates between most likely continuation (*𝜏*= 0), faithful sampling (*𝜏*= 1), and uniform sampling (*𝜏*= ∞). • **EDInference()** Algorithm 15 shows how to use a sequence-to-sequence transformer for prediction.

**Decoder-only transformers: GPT-2 \[RWC**[^+^](#page-10)**19\],** **GPT-3 \[BMR**[^+^](#page-9)**20\], Gopher \[RBC**[^+^](#page-10)**21\].** GPT-2 and GPT-3 are large language models developed by OpenAI, and Gopher is a large language model developed by DeepMind. They all have similar architectures and are trained by autoregressive language modelling: Given an incomplete sen- tence or paragraph, the goal is to predict the next token.

The main diﬀerence from BERT is that GPT/Gopher use unidirectional attention instead of bidirectional attention; they also apply layer- norms in slightly diﬀerent order.

See Algorithm 10 for the pseudocode of GPT-2. GPT-3 is identical except larger, and replaces dense attention in Line 6 by sparse attention, i.e. each token only uses a subset of the full context.

Gopher also deviates only slightly from the GPT-2 architecture: it replaces layer norm in lines 5, 7 and 10 by RMSnorm (*𝑚*= *𝜷*= 0), and it uses diﬀerent positional embeddings.

**Gradient descent.** The described training Algo- rithms 11 to 13 use Stochastic Gradient Descent

8

Formal Algorithms for Transformers

(SGD) *𝜽*←*𝜽*−*𝜂*· ∇loss(*𝜽*) to minimize the log loss (aka cross entropy) as the update rule. Com- putation of the gradient is done via automatic diﬀerentiation tools; see \[BPRS18, Table 5\]. In practice, vanilla SGD is usually replaced by some more reﬁned variation such as RMSProp or Ada- Grad or others \[Rud16\]. Adam \[KB15\] is used most often these days.

\[BFT17\] Peter L Bartlett, Dylan J Foster, and Ma- tus J Telgarsky. Spectrally-normalized margin bounds for neural networks. *NeurIPS*, 2017.

\[BMR+20\] Tom Brown, Benjamin Mann, Nick Ryder, et al. Language models are few-shot learners. *NeurIPS*, 2020.

\[BPRS18\] Atilim Gunes Baydin, Barak A. Pearl- mutter, Alexey Andreyevich Radul, and Jef- frey Mark Siskind. Automatic Diﬀerentiation in Machine Learning: A Survey. *Journal of Ma-* *chine Learning Research*, 18(153):1–43, 2018.

**8. Practical Considerations**

While the vanilla transformers provided here may work in practice, a variety of “tricks” have been developed over the years to improve the perfor- mance of deep neural networks in general and transformers in particular \[LWLQ21\]:

\[DCLT19\] Jacob Devlin, Ming-Wei Chang, Ken- ton Lee, and Kristina Toutanova. BERT: Pre- training of deep bidirectional transformers for language understanding. *ACL*, 2019.

- **Data preprocessing:** cleaning, augmen- tation \[FGW+21\], adding noise, shuﬄing \[Lem21\] (besides tokenization and chunk- ing). • **Architecture:** sparse layers, weight sharing (besides attention). • **Training:** improved optimizers, mini- batches, batch normalization, learning rate scheduling, weight initialization, pre- training, ensembling, multi-task, adversarial (besides layer normalization) \[Sut15\]. • **Regularization:** weight decay, early stop- ping, cross-validation, dropout, adding noise \[MBM20, TZ22\]. • **Inference:** scratchpad prompting, few-shot prompting, chain of thought, majority voting \[LAD+22\]. • **Others.**

    \[EGKZ21\] Benjamin L. Edelman, Surbhi Goel, Sham Kakade, and Cyril Zhang. Inductive Bi- ases and Variable Creation in Self-Attention Mechanisms. *arXiv:2110.10090 \[cs, stat\]*, Oc- tober 2021.

    \[Elh21\] Nelson Elhage. A Math- ematical Framework for Trans- former Circuits. https://transformer- circuits.pub/2021/framework/index.html, 2021.

    \[EMK+21\] Yonathan Efroni, Dipendra Misra, Ak- shay Krishnamurthy, Alekh Agarwal, and John Langford. Provable RL with Exogenous Distrac- tors via Multistep Inverse Dynamics, March 2021.

    \[FGW+21\] Steven Y Feng, Varun Gangal, Ja- son Wei, Sarath Chandar, Soroush Vosoughi, Teruko Mitamura, and Eduard Hovy. A survey of data augmentation approaches for NLP. In *Findings of the Association for Computational* *Linguistics: ACL-IJCNLP 2021*, pages 968–988, 2021.

**A. References**

\[Ala18\] Jay Alammar. The Illustrated Trans- former. http://jalammar.github.io/illustrated- transformer/, 2018.

\[Gag94\] Philip Gage. A new algorithm for data compression. *Dr. Dobbs / C Users Journal*, 12(2):23–38, 1994.

\[Ala19\] Jay Alammar. The Illustrated GPT- 2 (Visualizing Transformer Language Mod- els). http://jalammar.github.io/illustrated- gpt2/, 2019.

\[JGH18\] Arthur Jacot, Franck Gabriel, and Clé- ment Hongler. Neural tangent kernel: Conver- gence and generalization in neural networks. *NeurIPS*, 2018.

\[Bel21\] Fabrice Bellard. NNCP v2: Loss- less Data Compression with Transformer. https://bellard.org/libnc/gpt2tc.html, 2021.

9

Formal Algorithms for Transformers

\[Rud16\] Sebastian Ruder. An overview of gradient descent optimization algo- rithms. https://ruder.io/optimizing-gradient- descent/, January 2016.

\[KB15\] Diederik Kingma and Jimmy Ba. Adam: A method for stochastic optimization. *ICLR*, 2015.

\[Ker21\] Jonathan Kernes. Mas- ter Positional Encoding: Part I. https://towardsdatascience.com/master- positional-encoding-part-i-63c05d90a0c3, March 2021.

\[RWC+19\] Alec Radford, Jeﬀrey Wu, Rewon Child, David Luan, Dario Amodei, and Ilya Sutskever. Language models are unsupervised multitask learners. *OpenAI blog*, 2019.

\[RZP+22\] Scott Reed, Konrad Żołna, Emilio Parisotto, et al. A generalist agent. *arXiv:2205.06175*, 2022.

\[LAD+22\] Aitor Lewkowycz, Anders An- dreassen, David Dohan, Ethan Dyer, Henryk Michalewski, Vinay Ramasesh, Ambrose Slone, Cem Anil, Imanol Schlag, Theo Gutman-Solo, Yuhuai Wu, Behnam Neyshabur, Guy Gur-Ari, and Vedant Misra. Solving Quantitative Reasoning Problems with Language Models. *arXiv:2206.14858 \[cs\]*, June 2022.

\[SBB18\] Richard S. Sutton, Andrew G. Barto, and Francis Bach. *Reinforcement Learning:* *An Introduction*. MIT Press, Cambridge, Mas- sachusetts, second edition edition edition, November 2018.

\[Lem21\] Chris Lemke. Data preprocessing in NLP. https://towardsdatascience.com/data- preprocessing-in-nlp-c371d53ba3e0, July 2021.

\[SGBK+21\] Eren Sezener, Agnieszka Grabska- Barwińska, Dimitar Kostadinov, Maxime Beau, Sanjukta Krishnagopal, David Budden, Mar- cus Hutter, Joel Veness, Matthew Botvinick, Claudia Clopath, Michael Häusser, and Peter E. Latham. A rapid and eﬃcient learning rule for biological neural circuits. Technical report, DeepMind, London, UK, 2021.

\[LWLQ21\] Tianyang Lin, Yuxin Wang, Xi- angyang Liu, and Xipeng Qiu. A Survey of Transformers, June 2021.

\[MBM20\] Reza Moradi, Reza Berangi, and Behrouz Minaei. A survey of regularization strategies for deep models. *Artiﬁcial Intelli-* *gence Review*, 53(6):3947–3986, August 2020.

\[SHB16\] Rico Sennrich, Barry Haddow, and Alexandra Birch. Neural machine translation of rare words with subword units. In *54th* *Annual Meeting of the Association for Compu-* *tational Linguistics*, pages 1715–1725. Asso- ciation for Computational Linguistics (ACL), 2016.

\[MKS+13\] Volodymyr Mnih, Koray Kavukcuoglu, David Silver, Alex Graves, Ioannis Antonoglou, Daan Wierstra, and Martin Riedmiller. Play- ing Atari with Deep Reinforcement Learning, December 2013.

\[Sut15\] Ilya Sutskever. A Brief Overview of Deep Learning. http://yyue.blogspot.com/2015/01/a- brief-overview-of-deep-learning.html, January 2015.

\[MPCB14\] Guido F Montufar, Razvan Pascanu, Kyunghyun Cho, and Yoshua Bengio. On the number of linear regions of deep neural net- works. *NeurIPS*, 2014.

\[TZ22\] Yingjie Tian and Yuqi Zhang. A compre- hensive survey on regularization strategies in machine learning. *Information Fusion*, 80:146– 166, April 2022.

\[PH22\] M. Phuong and M. Hutter. Formal al- gorithms for transformers. Technical report, DeepMind, London, UK, 2022. LaTeX source available at http://arXiv.org

\[VSP+17\] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. Attention is all you need. *NeurIPS*, 2017.

\[RBC+21\] Jack W. Rae, Sebastian Borgeaud, Trevor Cai, et al. Scaling language models: Methods, analysis & insights from training go- pher. *arXiv:2112.11446*, 2021.

10

Formal Algorithms for Transformers

### Algorithm 8: 𝑷←`EDTransformer`(𝒛, 𝒙|𝜽)

`/* Encoder-decoder transformer forward pass` `*/` **Input:** *𝒛, 𝒙*∈*𝑉*^∗, two sequences of token IDs.^ **Output:** *𝑷*∈(0*,* 1)*^𝑁^*^V×length(^*^𝒙^*^), where the^ *𝑡*-th column of *𝑷*represents ˆ*𝑃𝜽*(*𝑥*\[*𝑡*+ 1\]| *𝒙*\[1 : *𝑡*\]*, 𝒛*). **Hyperparameters:** *ℓ*max*, 𝐿*enc*, 𝐿*dec*, 𝐻, 𝑑*e*, 𝑑*mlp ∈ℕ **Parameters:** *𝜽*includes all of the following parameters: *𝑾𝒆*∈ℝ*^𝑑^*^e×^*^𝑁^*^V,^ *𝑾𝒑*∈ℝ*^𝑑^*^e×^*^ℓ^*^max, the token and positional embedding matrices.^ For *𝑙*∈\[*𝐿*enc\]: | **W**^enc^ *𝑙* , multi-head encoder attention parameters for layer *𝑙*, see (4), | *𝜸*^1^ *𝑙, 𝜷*^1^ *𝑙, 𝜸*^2^ *𝑙, 𝜷*^2^ *𝑙*^∈ℝ^*^𝑑^*^e, two sets of layer-norm parameters,^ | *𝑾𝑙* mlp1 ∈ℝ*^𝑑^*^mlp×^*^𝑑^*^e,^ *^𝒃𝑙^* mlp1 ∈ℝ*^𝑑^*^mlp,^ *^𝑾𝑙^* mlp2 ∈ℝ*^𝑑^*^e×^*^𝑑^*^mlp,^ *^𝒃𝑙^* mlp2 ∈ℝ*^𝑑^*^e, MLP parameters.^

For *𝑙*∈\[*𝐿*dec\]: | **W**^dec^ *𝑙* , multi-head decoder attention parameters for layer *𝑙*, see (4),

| **W**^e/d^ *𝑙* , multi-head cross-attention parameters for layer *𝑙*, see (4), | *𝜸*^3^ *𝑙, 𝜷*^3^ *𝑙, 𝜸*^4^ *𝑙, 𝜷*^4^ *𝑙, 𝜸*^5^ *𝑙, 𝜷*^5^ *𝑙*^∈ℝ^*^𝑑^*^e, three sets of layer-norm parameters,^ | *𝑾𝑙* mlp3 ∈ℝ*^𝑑^*^mlp×^*^𝑑^*^e,^ *^𝒃𝑙^* mlp3 ∈ℝ*^𝑑^*^mlp,^ *^𝑾𝑙^* mlp4 ∈ℝ*^𝑑^*^e×^*^𝑑^*^mlp,^ *^𝒃𝑙^* mlp4 ∈ℝ*^𝑑^*^e, MLP parameters.^

*𝑾𝒖*∈ℝ*^𝑁^*^V×^*^𝑑^*^e, the unembedding matrix.^ `/* Encode the context sequence:` `*/`

**1** *ℓ*z ←length(*𝒛*)

### 2 for 𝑡∈\[ℓz\] : 𝒆𝑡←𝑾𝒆\[:, 𝑧\[𝑡\]\] + 𝑾𝒑\[:, 𝑡\]

**3** *𝒁*←\[*𝒆*1*, 𝒆*2*, . . . 𝒆ℓ*z\]

**4 for** *𝑙*= 1*,* 2*, . . . , 𝐿*enc **do**

**5** *𝒁*←*𝒁*+ `MHAttention`(*𝒁*|**W**^enc^ *𝑙* *,* Mask ≡1)

**6** for *𝑡*∈\[*ℓ*z\] : *𝒁*\[:*, 𝑡*\] ←`layer_norm`(*𝒁*\[:*, 𝑡*\] | *𝜸*^1^ *𝑙, 𝜷*^1^ *𝑙*^)^

**7** *𝒁*←*𝒁*+ *𝑾𝑙* mlp2^`ReLU`^^(^*^𝑾𝑙^* mlp1*^𝒁^*^+^ *^𝒃𝑙^* mlp1**^1^**^⊺) +^ *^𝒃𝑙^* mlp2**^1^**^⊺^

**8** for *𝑡*∈\[*ℓ*z\] : *𝒁*\[:*, 𝑡*\] ←`layer_norm`(*𝒁*\[:*, 𝑡*\] | *𝜸*^2^ *𝑙, 𝜷*^2^ *𝑙*^)^

### 9 end

```
/* Decode the primary sequence, conditioning on the context:
*/
```

**10** *ℓ*x ←length(*𝒙*)

### 11 for 𝑡∈\[ℓx\] : 𝒆𝑡←𝑾𝒆\[:, 𝑥\[𝑡\]\] + 𝑾𝒑\[:, 𝑡\]

**12** *𝑿*←\[*𝒆*1*, 𝒆*2*, . . . 𝒆ℓ*x\]

**13 for** *𝑖*= 1*,* 2*, . . . , 𝐿*dec **do**

**14** *𝑿*←*𝑿*+ `MHAttention`(*𝑿*|**W**^dec^ *𝑙* *,* Mask\[*𝑡, 𝑡*^′\] ≡\[\[^*𝑡*≤*𝑡*^′\]\])^

**15** for *𝑡*∈\[*ℓ*x\] : *𝑿*\[:*, 𝑡*\] ←`layer_norm`(*𝑿*\[:*, 𝑡*\] | *𝜸*^3^ *𝑙, 𝜷*^3^ *𝑙*^)^

**16** *𝑿*←*𝑿*+ `MHAttention`(*𝑿, 𝒁*|**W**^e/d^ *𝑙* *,* Mask ≡1)

**17** for *𝑡*∈\[*ℓ*x\] : *𝑿*\[:*, 𝑡*\] ←`layer_norm`(*𝑿*\[:*, 𝑡*\] | *𝜸*^4^ *𝑙, 𝜷*^4^ *𝑙*^)^

**18** *𝑿*←*𝑿*+ *𝑾𝑙* mlp4^`ReLU`^^(^*^𝑾𝑙^* mlp3*^𝑿^*^+^ *^𝒃𝑙^* mlp3**^1^**^⊺) +^ *^𝒃𝑙^* mlp4**^1^**^⊺^

**19** for *𝑡*∈\[*ℓ*x\] : *𝑿*\[:*, 𝑡*\] ←`layer_norm`(*𝑿*\[:*, 𝑡*\] | *𝜸*^5^ *𝑙, 𝜷*^5^ *𝑙*^)^

### 20 end

```
/* Derive conditional probabilities and return:
*/
```

### 21 return 𝑷= softmax(𝑾𝒖𝑿)

11

Formal Algorithms for Transformers

### Algorithm 9: 𝑷←`ETransformer`(𝒙|𝜽)

`/* BERT, an encoder-only transformer, forward pass` `*/` **Input:** *𝒙*∈*𝑉*^∗, a sequence of token IDs.^ **Output:** *𝑷*∈(0*,* 1)*^𝑁^*^V×length(^*^𝒙^*^), where each column of^ *𝑷*is a distribution over the vocabulary. **Hyperparameters:** *ℓ*max*, 𝐿, 𝐻, 𝑑*e*, 𝑑*mlp*, 𝑑*f ∈ℕ **Parameters:** *𝜽*includes all of the following parameters: *𝑾𝒆*∈ℝ*^𝑑^*^e×^*^𝑁^*^V,^ *𝑾𝒑*∈ℝ*^𝑑^*^e×^*^ℓ^*^max, the token and positional embedding matrices.^ For *𝑙*∈\[*𝐿*\]: | **W***𝑙*, multi-head attention parameters for layer *𝑙*, see (4), | *𝜸*^1^ *𝑙, 𝜷*^1^ *𝑙, 𝜸*^2^ *𝑙, 𝜷*^2^ *𝑙*^∈ℝ^*^𝑑^*^e, two sets of layer-norm parameters,^ | *𝑾𝑙* mlp1 ∈ℝ*^𝑑^*^mlp×^*^𝑑^*^e,^ *^𝒃𝑙^* mlp1 ∈ℝ*^𝑑^*^mlp,^ *^𝑾𝑙^* mlp2 ∈ℝ*^𝑑^*^e×^*^𝑑^*^mlp,^ *^𝒃𝑙^* mlp2 ∈ℝ*^𝑑^*^e, MLP parameters.^

*𝑾𝒇*∈ℝ*^𝑑^*^f×^*^𝑑^*^e^*, 𝒃𝒇*∈ℝ*^𝑑^*^f,^ *𝜸, 𝜷*∈ℝ*^𝑑^*^f, the ﬁnal linear projection and layer-norm parameters.^ *𝑾𝒖*∈ℝ*^𝑁^*^V×^*^𝑑^*^e, the unembedding matrix.^

**1** *ℓ*←length(*𝒙*)

### 2 for 𝑡∈\[ℓ\] : 𝒆𝑡←𝑾𝒆\[:, 𝑥\[𝑡\]\] + 𝑾𝒑\[:, 𝑡\]

**3** *𝑿*←\[*𝒆*1*, 𝒆*2*, . . . 𝒆ℓ*\]

**4 for** *𝑙*= 1*,* 2*, . . . , 𝐿***do**

### 5 𝑿←𝑿+ `MHAttention`(𝑿|W𝑙, Mask ≡1)

**6** for *𝑡*∈\[*ℓ*\] : *𝑿*\[:*, 𝑡*\] ←`layer_norm`(*𝑿*\[:*, 𝑡*\] | *𝜸*^1^ *𝑙, 𝜷*^1^ *𝑙*^)^

**7** *𝑿*←*𝑿*+ *𝑾𝑙* mlp2^`GELU`^^(^*^𝑾𝑙^* mlp1*^𝑿^*^+^ *^𝒃𝑙^* mlp1**^1^**^⊺) +^ *^𝒃𝑙^* mlp2**^1^**^⊺^

**8** for *𝑡*∈\[*ℓ*\] : *𝑿*\[:*, 𝑡*\] ←`layer_norm`(*𝑿*\[:*, 𝑡*\] | *𝜸*^2^ *𝑙, 𝜷*^2^ *𝑙*^)^

### 9 end

**10** *𝑿*←`GELU`(*𝑾𝒇𝑿*+ *𝒃𝒇***1**^⊺)^

### 11 for 𝑡∈\[ℓ\] : 𝑿\[:, 𝑡\] ←`layer_norm`(𝑿\[:, 𝑡\] | 𝜸, 𝜷)

### 12 return 𝑷= softmax(𝑾𝒖𝑿)

12

Formal Algorithms for Transformers

### Algorithm 10: 𝑷←`DTransformer`(𝒙|𝜽)

`/* GPT, a decoder-only transformer, forward pass` `*/` **Input:** *𝒙*∈*𝑉*^∗, a sequence of token IDs.^ **Output:** *𝑷*∈(0*,* 1)*^𝑁^*^V×length(^*^𝒙^*^), where the^ *𝑡*-th column of *𝑷*represents ˆ*𝑃𝜽*(*𝑥*\[*𝑡*+ 1\]| *𝒙*\[1 : *𝑡*\]). **Hyperparameters:** *ℓ*max*, 𝐿, 𝐻, 𝑑*e*, 𝑑*mlp ∈ℕ **Parameters:** *𝜽*includes all of the following parameters: *𝑾𝒆*∈ℝ*^𝑑^*^e×^*^𝑁^*^V,^ *𝑾𝒑*∈ℝ*^𝑑^*^e×^*^ℓ^*^max, the token and positional embedding matrices.^ For *𝑙*∈\[*𝐿*\]: | **W***𝑙*, multi-head attention parameters for layer *𝑙*, see (4), | *𝜸*^1^ *𝑙, 𝜷*^1^ *𝑙, 𝜸*^2^ *𝑙, 𝜷*^2^ *𝑙*^∈ℝ^*^𝑑^*^e, two sets of layer-norm parameters,^ | *𝑾𝑙* mlp1 ∈ℝ*^𝑑^*^mlp×^*^𝑑^*^e,^ *^𝒃𝑙^* mlp1 ∈ℝ*^𝑑^*^mlp,^ *^𝑾𝑙^* mlp2 ∈ℝ*^𝑑^*^e×^*^𝑑^*^mlp,^ *^𝒃𝑙^* mlp2 ∈ℝ*^𝑑^*^e, MLP parameters.^

*𝜸, 𝜷*∈ℝ*^𝑑^*^e, ﬁnal layer-norm parameters.^ *𝑾𝒖*∈ℝ*^𝑁^*^V×^*^𝑑^*^e, the unembedding matrix.^

**1** *ℓ*←length(*𝒙*)

### 2 for 𝑡∈\[ℓ\] : 𝒆𝑡←𝑾𝒆\[:, 𝑥\[𝑡\]\] + 𝑾𝒑\[:, 𝑡\]

**3** *𝑿*←\[*𝒆*1*, 𝒆*2*, . . . 𝒆ℓ*\]

**4 for** *𝑙*= 1*,* 2*, . . . , 𝐿***do**

**5** for *𝑡*∈\[*ℓ*\] : **˜***𝑿*\[:*, 𝑡*\] ←`layer_norm`(*𝑿*\[:*, 𝑡*\] | *𝜸*^1^ *𝑙, 𝜷*^1^ *𝑙*^)^

### 6 𝑿←𝑿+ `MHAttention`( ˜𝑿|W𝑙, Mask\[𝑡, 𝑡^′\] = \[\[^𝑡≤𝑡^′\]\])^

**7** for *𝑡*∈\[*ℓ*\] : **˜***𝑿*\[:*, 𝑡*\] ←`layer_norm`(*𝑿*\[:*, 𝑡*\] | *𝜸*^2^ *𝑙, 𝜷*^2^ *𝑙*^)^

**8** *𝑿*←*𝑿*+ *𝑾𝑙* mlp2^`GELU`^^(^*^𝑾𝑙^* mlp1 **˜***^𝑿^*^+^ *^𝒃𝑙^* mlp1**^1^**^⊺) +^ *^𝒃𝑙^* mlp2**^1^**^⊺^

### 9 end

### 10 for 𝑡∈\[ℓ\] : 𝑿\[:, 𝑡\] ←`layer_norm`(𝑿\[:, 𝑡\] | 𝜸, 𝜷)

### 11 return 𝑷= softmax(𝑾𝒖𝑿)

13

Formal Algorithms for Transformers

**Algorithm 11:** ˆ*𝜽*←`EDTraining`(*𝒛*1:*𝑁*data*, 𝒙*1:*𝑁*data*, 𝜽*)

`/* Training a seq2seq model` `*/` **Input:** {(*𝒛𝑛, 𝒙𝑛*)}*^𝑁^*^data^ *𝑛*=1 , a dataset of sequence pairs. **Input:** *𝜽*, initial transformer parameters. **Output:** ˆ*𝜽*, the trained parameters. **Hyperparameters:** *𝑁*epochs ∈ℕ*, 𝜂*∈(0*,* ∞)

### Algorithm 13: ˆ𝜽←`DTraining`(𝒙1:𝑁data, 𝜽)

`/* Training next token prediction` `*/` **Input:** {*𝒙𝑛*}*^𝑁^*^data^ *𝑛*=1 , a dataset of sequences. **Input:** *𝜽*, initial decoder-only transformer parameters. **Output:** ˆ*𝜽*, the trained parameters. **Hyperparameters:** *𝑁*epochs ∈ℕ*, 𝜂*∈(0*,* ∞)

**1 for** *𝑖*= 1*,* 2*, . . . , 𝑁*epochs **do**

**2** **for** *𝑛*= 1*,* 2*, . . . 𝑁*data **do**

**3** *ℓ*←length(*𝒙𝑛*)

**1 for** *𝑖*= 1*,* 2*, . . . , 𝑁*epochs **do**

**4** *𝑷*(*𝜽*) ←`EDTransformer`(*𝒛𝑛, 𝒙𝑛*|*𝜽*)

**2** **for** *𝑛*= 1*,* 2*, . . . 𝑁*data **do**

**5** loss(*𝜽*) = −Í*^ℓ^*^−1^ *𝑡*=1 log *^𝑃^*^(^*^𝜽^*^)\[^*^𝑥𝑛^*^\[^*^𝑡^*^+1\]^*^, 𝑡^*^\]^

**3** *ℓ*←length(*𝒙𝑛*)

### 6 𝜽←𝜽−𝜂· ∇loss(𝜽)

**4** *𝑷*(*𝜽*) ←`DTransformer`(*𝒙𝑛*| *𝜽*)

**5** loss(*𝜽*) = −Í*^ℓ^*^−1^ *𝑡*=1 log *^𝑃^*^(^*^𝜽^*^)\[^*^𝑥𝑛^*^\[^*^𝑡^*^+1\]^*^, 𝑡^*^\]^

### 7 end

### 6 𝜽←𝜽−𝜂· ∇loss(𝜽)

### 8 end

### 9 return ˆ𝜽= 𝜽

### 7 end

### 8 end

### 9 return ˆ𝜽= 𝜽

### Algorithm 12: ˆ𝜽←`ETraining`(𝒙1:𝑁data, 𝜽)

`/* Training by masked language` `modelling` `*/` **Input:** {*𝒙𝑛*}*^𝑁^*^data^ *𝑛*=1 , a dataset of sequences. **Input:** *𝜽*, initial encoder-only transformer parameters. **Output:** ˆ*𝜽*, the trained parameters. **Hyperparameters:** *𝑁*epochs ∈ℕ*, 𝜂*∈ (0*,* ∞)*, 𝑝*mask ∈(0*,* 1)

### Algorithm 14: 𝒚←`DInference`(𝒙, ˆ𝜽)

`/* Prompting a trained model and using` `it for prediction.` `*/` **Input:** Trained transformer parameters ˆ*𝜽*. **Input:** *𝒙*∈*𝑉*^∗, a prompt.^ **Output:** *𝒚*∈*𝑉*^∗, the transformer’s^ continuation of the prompt. **Hyperparameters:** *ℓ*gen ∈ℕ*, 𝜏*∈(0*,* ∞)

**1 for** *𝑖*= 1*,* 2*, . . . , 𝑁*epochs **do**

**2** **for** *𝑛*= 1*,* 2*, . . . , 𝑁*data **do**

**3** *ℓ*←length(*𝒙𝑛*)

**4** **for** *𝑡*= 1*,* 2*, . . . , ℓ***do**

**5** ˜*𝑥𝑛*\[*𝑡*\] ←`mask_token` or *𝑥𝑛*\[*𝑡*\] randomly with probability *𝑝*mask or 1 −*𝑝*mask

**1** *ℓ*←length(*𝒙*)

### 2 for 𝑖= 1, 2, . . . ℓgen do

**3** *𝑷*←`DTransformer`(*𝒙*| ˆ*𝜽*)

### 6 end

### 7 ˜𝑇←{𝑡∈\[ℓ\] : ˜𝑥𝑛\[𝑡\] = `mask_token`}

**4** *𝒑*←*𝑷*\[:*, ℓ*+ *𝑖*−1\]

**5** sample a token *𝑦*from *𝒒*∝*𝒑*^1/^*^𝜏^*

**8** *𝑷*(*𝜽*) ←`ETransformer`(**˜***𝒙𝑛*| *𝜽*)

**9** loss(*𝜽*) = −Í *𝑡*∈˜*𝑇*^log^ *^𝑃^*^(^*^𝜽^*^)\[^*^𝑥𝑛^*^\[^*^𝑡^*^\]^*^, 𝑡^*^\]^

**6** *𝒙*←\[*𝒙, 𝑦*\]

### 10 𝜽←𝜽−𝜂· ∇loss(𝜽)

### 7 end

### 11 end

### 8 return 𝒚= 𝒙\[ℓ+ 1 : ℓ+ ℓgen\]

### 12 end

### 13 return ˆ𝜽= 𝜽

14

Formal Algorithms for Transformers

### Algorithm 15: ˆ𝒙←`EDInference`(𝒛, ˆ𝜽)

`/* Using a trained seq2seq model for` `prediction.` `*/` **Input:** A seq2seq transformer and trained parameters ˆ*𝜽*of the transformer. **Input:** *𝒛*∈*𝑉*^∗, input sequence, e.g. a^ sentence in English. **Output: ˆ***𝒙*∈*𝑉*^∗, output sequence, e.g. the^ sentence in German. **Hyperparameters:** *𝜏*∈(0*,* ∞)

**1 ˆ***𝒙*←\[`bos_token`\]

**2** *𝑦*←0

### 3 while 𝑦≠`eos_token` do

**4** *𝑷*←`EDTransformer`(*𝒛,* **ˆ***𝒙*| ˆ*𝜽*)

**5** *𝒑*←*𝑷*\[:*,* length(**ˆ***𝒙***)**\]

**6** sample a token *𝑦*from *𝒒*∝*𝒑*^1/^*^𝜏^*

### 7 ˆ𝒙←\[ˆ𝒙, 𝑦\]

### 8 end

### 9 return ˆ𝒙

15

Formal Algorithms for Transformers

**B. List of Notation**

**Symbol** **Type** **Explanation** \[*𝑁*\] := {1*, ..., 𝑁*} set of integers 1*,* 2*, ..., 𝑁*−1*, 𝑁* *𝑖, 𝑗* ∈ℕ generic integer indices *𝑉*  \[*𝑁*V\] vocabulary *𝑁*V ∈ℕ vocabulary size *𝑉*^∗^ = Ð∞ *ℓ*=0 *𝑉ℓ* set of token sequences; elements include e.g. sentences or documents *ℓ*max ∈ℕ maximum sequence length *ℓ* ∈\[*ℓ*max\] length of token sequence *𝑡* ∈\[*ℓ*\] index of token in a sequence *𝑑...* ∈ℕ dimension of various vectors *𝒙* ≡*𝑥*\[1 : *ℓ*\] ≡*𝑥*\[1\]*𝑥*\[2\]*...𝑥*\[*ℓ*\] ∈*𝑉ℓ* primary token sequence *𝒛* ≡*𝑧*\[1 : *ℓ*\] ≡*𝑧*\[1\]*𝑧*\[2\]*...𝑧*\[*ℓ*\] ∈*𝑉ℓ* context token sequence *𝑀*\[*𝑖, 𝑗*\] ∈ℝ entry *𝑀𝑖𝑗*of matrix *𝑀*∈ℝ*^𝑑^*^×^*^𝑑^*^′^

*𝑀*\[*𝑖,* :\] ≡*𝑀*\[*𝑖*\] ∈ℝ*^𝑑^*^′^ *𝑖*-th row of matrix *𝑀*∈ℝ*^𝑑^*^×^*^𝑑^*^′^

*𝑀*\[:*, 𝑗*\] ∈ℝ*^𝑑^* *𝑗*-th column of matrix *𝑀*∈ℝ*^𝑑^*^×^*^𝑑^*^′^

*𝒆* ∈ℝ*^𝑑^*^e^ vector representation / embedding of a token *𝑿* ∈ℝ*^𝑑^*^e×^*^ℓ𝑥^* encoded primary token sequence *𝒁* ∈ℝ*^𝑑^*^e×^*^ℓ𝑧^* encoded context token sequence Mask ∈ℝ*^ℓ𝑧^*^×^*^ℓ𝑥^* masking matrix, it determines the attention context for each token *𝐿, 𝐿*enc*, 𝐿*dec ∈ℕ number of network (encoder, decoder) layers *𝑙* ∈\[*𝐿*\] index of network layer *𝐻* ∈ℕ number of attention heads *ℎ* ∈\[*𝐻*\] index of attention head *𝑁*data ∈ℕ (i.i.d.) sample size *𝑛* ∈\[*𝑁*data\] index of sample sequence *𝜂* ∈(0*,* ∞) learning rate *𝜏* ∈(0*,* ∞) temperature; it controls the diversity-plausibility trade-oﬀat inference *𝑾𝒆* ∈ℝ*^𝑑^*^e×^*^𝑁^*^V^ token embedding matrix *𝑾𝒑* ∈ℝ*^𝑑^*^e×^*^ℓ^*^max^ positional embedding matrix *𝑾𝒖* ∈ℝ*^𝑁^*^V×^*^𝑑^*^e^ unembedding matrix *𝑾𝒒* ∈ℝ*^𝑑^*^attn×^*^𝑑^*^x^ query weight matrix *𝒃𝒒* ∈ℝ*^𝑑^*^attn^ query bias *𝑾𝒌* ∈ℝ*^𝑑^*^attn×^*^𝑑^*^z^ key weight matrix *𝒃𝒌* ∈ℝ*^𝑑^*^attn^ key bias *𝑾𝒗* ∈ℝ*^𝑑^*^out×^*^𝑑^*^z^ value weight matrix *𝒃𝒗* ∈ℝ*^𝑑^*^out^ value bias **W***𝒒𝒌𝒗* collection of above parameters of a single-head attention layer *𝑾𝒐* ∈ℝ*^𝑑^*^out×^*^𝐻𝑑^*^mid output weight matrix^ *𝒃𝒐* ∈ℝ*^𝑑^*^out^ output bias **W** collection of above parameters of a multi-head attention layer, see eq. (4) *𝑾***mlp** ∈ℝ*^𝑑^*^1×^*^𝑑^*^2^ weight matrix corresponding to an MLP layer in a Transformer *𝒃***mlp** ∈ℝ*^𝑑^*^1^ bias corresponding to an MLP layer in a Transformer *𝜸* ∈ℝ*^𝑑^*^e^ layer-norm learnable scale parameter *𝜷* ∈ℝ*^𝑑^*^e^ layer-norm learnable oﬀset parameter *𝜽,* ˆ*𝜽* ∈ℝ*^𝑑^* collection of all learnable / learned Transformer parameters

16