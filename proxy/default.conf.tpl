server { # this block defines the settings for the server or group of servers
    listen ${LISTEN_PORT}; # This specifies the port on which the server will listen for
    # incomming connections

    location /static { #This defines the location directive for the requests that starts with /static
        #This is commonly used for serving static files.
        alias /vol/static; # path where nginx looks for static files
    }

    location / { # location directive for the root path
        uwsgi_pass            ${APP_HOST}:${APP_PORT}; # pass request to the uwsgi server for processing
        include               /etc/nginx/uwsgi_params;
        client_max_body_size  10M; # maximum allowed size of the client request body.
    }
}