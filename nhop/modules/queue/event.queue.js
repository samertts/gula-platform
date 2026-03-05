// modules/queue/event.queue.js

const eventQueue = [];

function addEvent(event) {
  eventQueue.push(event);
  console.log("EVENT ADDED TO QUEUE");
}

function getNextEvent() {
  return eventQueue.shift();
}

function hasEvents() {
  return eventQueue.length > 0;
}

module.exports = {
  addEvent,
  getNextEvent,
  hasEvents
};
