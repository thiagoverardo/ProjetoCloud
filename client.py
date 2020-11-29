import click
import requests
import json

urlLB = "http://ThiagoLB-1540369818.us-east-1.elb.amazonaws.com:8080/tasks/"


@click.command()
@click.option("-i", "--instruction", default="GET")
@click.option("-t", "--title", default="foo")
@click.option("-p", "--pub_date", default="2000-11-27T00:00:00Z")
@click.option("-d", "--description", default="bar")
def command(instruction, title, pub_date, description):

    if instruction == "GET":
        r = requests.get(urlLB + "getTasks")
        print(r.text)

    if instruction == "POST":
        json_input = {
            "title": title,
            "pub_date": pub_date,
            "description": description,
        }
        r = requests.post(urlLB + "postTask", data=json.dumps(json_input))
        print(r.text)

    if instruction == "DELETE":
        r = requests.delete(urlLB + "deleteTasks")
        r = requests.get(urlLB + "getTasks")
        print(r.text)


if __name__ == "__main__":
    command()