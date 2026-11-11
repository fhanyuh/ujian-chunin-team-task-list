# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Plain HTML5, CSS, and Vanilla JavaScript (`index.html`) served by Nginx (`nginx:1.27-alpine`), communicating asynchronously via `fetch()` with a Python standard-library REST API (`app.py`).

## Users

Small project or study teams (such as our 4-member team: Rafhan Mazaya Fathurrahman, Zahra Talitha Putri, Clara Novita Fitriani, and Rafif Riqullah Siregar) who need a shared, straightforward workspace to track group tasks, assignees, deadlines, and progress notes without clutter.

## Product Purpose

**Papan Catatan Tugas Kelompok** lets a team capture tasks and notes, assign them to team members, track status (`Todo`, `In Progress`, `Done`) and priority (`High`, `Medium`, `Low`), filter by member or status, and remove completed items in real time.

## Positioning

A focused, zero-friction shared task board where adding a task, filtering by teammate, updating status, and removing finished work happen in one clean view without exposing underlying server or infrastructure jargon to the end user.

## Operating Context

Used in desktop and laptop web browsers (`https://cc.fhanmazaya.my.id` and `http://localhost:3000`) during daily team coordination and sprint check-ins.

## Capabilities and Constraints

- Add new team tasks with title, assignee, priority, initial status, category, due date, and notes (`POST /tasks`).
- View all tasks and team workload distribution (`GET /tasks`).
- Update task status (`PATCH /tasks?index=X`) and delete tasks in real time (`DELETE /tasks?index=X`).
- UI copy must stay purely user-facing and product-oriented: no HTTP status codes, container names, DNS paths, volume paths, or course/exam labels in the main interface; team identity sits quietly in the footer.

## Product Principles

1. **Pure user-facing language**: Speak in the user's task domain (tugas, catatan, anggota, tenggat), never in infrastructure or API terms.
2. **Immediate clarity**: Show who is responsible for what and what is still pending at a glance.
3. **One-screen flow**: Adding, filtering, updating, and deleting tasks happen in place without page reloads or modal mazes.
