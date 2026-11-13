FROM postgres:16.16-alpine3.24@sha256:0adbf25a9e96d38823bb813f3ac0ed41fadb665c88f1df7fe6dbfb060cbdc106

# The upstream gosu binary embeds a Go stdlib with high/critical findings.
# Alpine's MIT-licensed su-exec implements the user/group/exec call required by
# the unchanged official entrypoint. Replace only this helper in the new image.
RUN apk add --no-cache su-exec=0.3-r0 \
    && cp /sbin/su-exec /usr/local/bin/gosu \
    && test ! -L /usr/local/bin/gosu \
    && cmp /sbin/su-exec /usr/local/bin/gosu \
    && gosu postgres sh -c 'test "$(id -u)" = 70 && test "$(id -g)" = 70' \
    && gosu nobody true
