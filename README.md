# WavTouch

視覚障害者向け教材「音の形をさわってみよう」

概要
----
  * 音が波からできていることを教える。
  * 音の大きさ、音の高さ、音色がそれぞれ波形のどのような要素によって表現されるかを教える。

授業の流れ
----------
  1. まず、音が空気の振動であることを確認する。
  2. 最初に sine.wav を聴かせ、波形を作成させる。この縦のずれがスピーカー表面の動きをあらわしていることを説明する。10個の周期をもつことを確認させる。
  3. sine.wav は 480Hz の音であり、1秒間にこの周期が 480回繰り返されることを説明する。
     (なお、実際の音は 24000Hz でサンプリングされており、1周期は 50サンプルだが、ここでは 1/5 に縮小して見せかけている)
  4. soft1.wav, soft2.wav を観察する。音が小さくなると波形の振幅が小さくなることを確認させる。
  5. high1.wav, high2.wav を観察する。音が高くなると波形の変化が速くなることを確認させる。
  6. low1.wav, low2.wav を観察する。音が低くなると波形の変化が遅くなることを確認させる。
  7. mix.wav を観察する。これは high2.wav と low2.wav の和音であり、2つの波形成分が現れていることを確認させる。
  8. rect.wav, saw.wav を観察する。波形の振幅および周期は sine.wav と同じだが、音色が違っていることを確認させる。
  9. noise.wav を観察する。雑音は音の一種であるが、周期がないことを確認させる。
  10. 時間があれば、各生徒の声を録音して 24000Hz で保存し、観察させる。(Audacity などを使う)

必要なもの
----------
  * PC あるいは Raspberry Pi (人数分)
  * Python2 (あるいは Python3) および Pygame をインストールしておくこと

起動方法
--------

 1. なにか適当なフォント (.ttfファイル) をコピーしておく。
 2. 以下のように実行:
    $ python wavtouch.py -F フォントファイル名 音声ファイルディレクトリ
 3. 観察する音声ファイルディレクトリとして wavs/ を指定する。

操作方法
--------

  * Escapeキーで終了。
  * テンキーにより操作する。
  * 4/6 キー (または左右キー) で観察したい波形を選択する。
  * 5 キー (または Enterキー) でその波形を「開く」。
  * 波形が開いている時、4/6 キーでサンプルの数字をひとつずつたどることができる。
  * 現在位置がわからなくなった場合、8キーを押すと先頭に戻る。
  * BS キー (または TABキー) で波形選択画面に戻る。このとき波形一覧が refresh される。

サーバで波形を一元管理する
--------------------------

  * サブネット上で末尾が *.*.*.1 のアドレスで HTTP サーバを listen しておく。
    Windows の場合は以下の DHCP サーバを使う: http://www.dhcpserver.de/cms/ 
  * 以下の URL にアクセス可能にする:
    http://xxx.xxx.xxx.1/wavtouch/index.txt
  * この URL から上記の音声ファイル (index.txt および *.wav) がダウンロードできるようにしておく。
  * クライアントを以下の方法で起動する。
  
    $ python wavtouch.py -f //wavtouch/
