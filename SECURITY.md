# Security policy

## The guarantee

Turnbreak's server binds to `127.0.0.1` only. Nothing outside your machine can reach it. Your interests file, your reading history, and every item it shows you stay on disk. None of it is sent anywhere, except the network calls each source finder makes on your behalf to fetch the articles or search results you asked for.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting on this repository, under the Security tab. Don't open a public issue or pull request for a vulnerability. That page is for everything else.

## Report contents

Steps to reproduce, or a proof of concept. What you ran it against, including turnbreak's version. Anything it printed.

## Out of scope

A vulnerability here is a defect in turnbreak's own code that lets an attacker read or change something on your machine without already controlling it, or that makes the server reachable from anywhere but `127.0.0.1`. A source finder returning bad or unpleasant content isn't a vulnerability. That's a bug report instead.

## Supported versions

Turnbreak has one supported version: the latest release. There's no older version to maintain yet.

## AI-assisted reports

An AI tool can help you find or write up a vulnerability, but you're responsible for what you submit. Verify the tool's output before reporting it.
