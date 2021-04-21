# Asynchronous Microservices Demo Application

The app converts uploaded image into half-grayscale variant.

The demo application consists from 3 microservices:

* _Front-End_ - serves single web page to accept file upload and display result, interacting with "job manager" via
  Kafka topics
* _Job Manager_ - forwards image to "grayscaler" for processing, assembles resulting image from two variants
* _Grayscaler_ - get image via Kafka and sends back grayscale variant of it

![Overall App](app.png)

## Running Application Normally

On the top root directory of repository, just run it with docker-compose:

```shell
docker-compose up
```

The app will start up. You will see some warnings about topics not existing, this is normal because our Kafka is empty.

Now open in your browser [http://localhost/](http://localhost/) to see the application. Then upload a colorful image via web form and wait for resulting image to appear. 

Upload more images to get more results. Notice that after the first result the Kafka topics have been created and there are no more log warnings. In the log, you can see messages about different services working with Kafka topics.

To stop the application, press `Ctrl+C`.

## Running Front-End Isolated

Navigate to `frontend` subfolder, and run there `docker-compose up`. 

After it starts, open [http://localhost/](http://localhost/) in your browser and try uploading some images. Note how the resulting image is the same each time, originating from Mockintosh's configuration.

Open [http://localhost:8000/](http://localhost:8000/) to see the mocked Kafka traffic log in Mockintosh UI.

## Running Job Manager Isolated

Navigate to `manager` subfolder, and run there `docker-compose up`.

Open [http://localhost:8000/](http://localhost:8000/) to see the mocked Kafka traffic log in Mockintosh UI. Notice that each 5 seconds the new job is triggered automatically by Mockintosh's "scheduled producer".

## Running Grayscaler Isolated

Navigate to `grayscaler` subfolder, and run there `docker-compose up`.

Run the automated test in parallel console like this:

```shell
pytest -v tests.py
```

Open [http://localhost:8000/](http://localhost:8000/) and enable traffic logging to see messages produced and consumed by Mockintosh while `pytest` is running. Additionally, trigger some jobs for Grayscaler from "Async Actors" tab in Mockintosh UI.

## Running Without `docker-compose`

`docker run -d -it -p 9092:9092 up9inc/mockintosh:self-contained-kafka`