import io, zipfile

if __name__=="__main__":
    buf=io.BytesIO()
    with zipfile.ZipFile(buf, "a",
                         zipfile.ZIP_DEFLATED, False) as zf:
        for filename, data in [('hello.txt', "hello world"),
                               ('goodbye.txt', "goodbye cruel world!")]:
            zf.writestr(filename, data)
    with open('tmp/hello.zip', 'wb') as f:
        f.write(buf.getvalue())
