# childes_roles.json: what it is and its licence

`childes_roles.json` is the label-free role model `serve_return.blind`
uses: an averaged perceptron's weights over word, word-pair, length and
pause features, with the turn scale learned by cross-fitting. It was
trained on the transcripts of the CHILDES Gleason corpus. It holds
feature weights, not transcripts: no utterance, speaker or session is in
it.

Because it is derived from TalkBank data, this one file is licensed
differently from the rest of the package:

- **This file:** Creative Commons Attribution-NonCommercial-ShareAlike
  3.0 (CC BY-NC-SA 3.0), the licence TalkBank shares the corpus under,
  https://creativecommons.org/licenses/by-nc-sa/3.0/. Non-commercial use
  only; adaptations under the same licence; attribute as below.
- **Everything else in serve-return:** MIT.

TalkBank's rules preclude incorporating its data into commercial
products. serve-return and Volley are free and non-commercial. A
commercial use of label-free counting needs a model trained on data
licensed for it; `harness/blind/run.py --write-model` in the repository
trains one from any CHAT corpus.

The transcripts themselves were never committed, uploaded, or sent to
any service; they stay on the machine of whoever downloads them with
their own TalkBank account.

## Attribution, as TalkBank asks

- Gleason, J. B. CHILDES Gleason corpus. doi:10.21415/T5101R, retrieved 2026.
- Masur, E. F., and Gleason, J. B. (1980). Parent-child interaction and the
  acquisition of lexical information during play. Developmental Psychology,
  16(5), 404-409. doi:10.1037/0012-1649.16.5.404
- MacWhinney, B. (2000). The CHILDES Project: Tools for analyzing talk.
  Third edition. Mahwah, NJ: Lawrence Erlbaum Associates. CHILDES is
  supported by NICHD grant HD082736.
