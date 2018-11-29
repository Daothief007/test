
### sockjs server


### nginx proxy config:

```
    location /sockjs/ {
        proxy_pass http://127.0.0.1:18080;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_pass_header Server;
    }
```

### 使用：

1. 面向服务端接口有`init`与`push`。

`init`接口：

 * 调用方式： POST with json body.
 * 参数： 
     rt - request key.
     user_id - user id.
     token - token.

`rt`为接口授权key。
`user_id`代表用户的唯一ID。
`token`为`sockjs`中代表当前用户的标志，一个`user_id`可对应多个`token`。


`push`接口：

 * 调用方式： POST with json body.
 * 参数： 
     rt - request key.
     user_id - user id.
     content - 推送内容。

2. 面向客户端接口有`conn`（sockjs的`new SockJS()`中传的url）。

3. 测试链接：http://localhost:18080/sockjs/conn/info?t=af或者http://hostname/sockjs/conn/info?t=af