# はじめに


GoogleCloudコンソールで提供されているVertexAIStudioのチャットアプリケーション相当のものをstreamlitで実装したものです。あわせてGoogle App Engineにデプロイして利用できるようにしています。

GCPコンソールのvertexaiアプリやagent builder等が操作しづらい事業メンバー向けによりユーザライクになるアプリを作る目的で開発しました。
背景は[こちらの記事](https://qiita.com/1kjwk1/private/588e8dea9f9edcbe1ab5)をご覧ください。


# 使い方

pythonが実行できるmacを前提とします。
pythonの環境の他、GoogleCloudSDKを導入してgcloudコマンドが使える状態にする必要があります。
ローカルで実行する場合はgeminiを利用するため、gcloudコマンドで取得できる認証情報であるApplication Default Credentials (ADC) を利用します。

## Google Cloud SDKの導入

brewが導入されていればそのまま[brewで入れる](https://formulae.brew.sh/cask/google-cloud-sdk)のが手軽です。

``` sh
$ brew install --cask google-cloud-sdk
```
brewの説明ページの通り利用しているシェルにあわせて追加します。私はzshなので`.zshrc`に以下を追加します。
``` sh
source "$(brew --prefix)/share/google-cloud-sdk/path.zsh.inc"
source "$(brew --prefix)/share/google-cloud-sdk/completion.zsh.inc"
```

公式の場合は[こちら](https://cloud.google.com/sdk/docs/install?hl=ja)を参考にしてください。


取得したGCPプロジェクトに権限のあるgoogleアカウントで初期設定をします。

``` sh
$ gcloud init
```

## アプリケーションの起動

```
# pythonは3.11で動作確認してます(他でも動きそうです)。python仮想環境を使っている場合は適宜作成します
python -V
Python 3.11.9

# streamlitとgoogleaiを導入します
pip install -r requirements.txt

# ローカルで実行するためにADCを取得します（ブラウザが起動するのでgcpのログインしているブラウザでログインします）
gcloud auth application-default login

# webアプリを起動します
streamlit run main.py --server.port 8080
```

## ログイン

- 平文のパスワードをhash.py内の`password`にいれて実行してハッシュ化されたパスワードを`config.yaml`に設定します。
- `username`/`password`でログインします。

```
python hash.py
```

## GCPデプロイ

GCPにstreamlitアプリケーションを簡単にデプロイする方法としてはAppEngine/CloudRunの２択があげられます。
今回は急ぎなのもありより手頃なAppEngineにデプロイしました
streamlitアプリケーションはwebsocketを利用するためスタンダード環境ではなくflex環境を利用します。flex環境は最低１台でアクセスがない場合の自動停止等をしないので費用がかかります（１台運用で月１万弱程度）
[こちらの記事](https://sanshonoki.hatenablog.com/entry/2024/06/30/110626)をご覧ください。

`gcloud init`でGCPのSDKを設定して有効化したターミナルで以下コマンドでデプロイ

```
gcloud app deploy
```
