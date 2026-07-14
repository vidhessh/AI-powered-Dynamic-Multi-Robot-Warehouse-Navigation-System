#!/usr/bin/env python3
"""
lot_input_bot1.py — command-line target input for bot1 only, with
natural-language parsing via Groq, full-session memory, and a stop
command.

Namespaced to 'bot1', so publishing on 'target_lot' actually goes to
/bot1/target_lot, and 'lot_status' actually comes from /bot1/lot_status.

Every typed line is routed through Groq (llama-3.1-8b-instant) to
extract either a lot color, the word "stop", or "none". The FULL
session conversation (every command you've typed and what it resolved
to, since this node started) is included as context on every request,
so references like "go where you started" can resolve against
something said earlier in the session (e.g. it already saw "origin").

Saying "stop" (or "halt", "wait", "cancel", etc. — anything Groq maps
to stop intent) cancels whatever the bot is currently doing and holds
it in place until the next real command.

REQUIRES the GROQ_API_KEY environment variable to be set. Do NOT hardcode
your key in this file — export it in your shell profile instead:

    export GROQ_API_KEY="your-key-here"

If a command is ambiguous or names no valid lot, nothing is published —
the node just reprompts, same as an invalid command did before.
"""

import os
import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import requests

BOT_NAMESPACE = 'bot1'
VALID_LOTS = {"red", "green", "blue", "yellow", "origin"}
STOP_WORD = "stop"

GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """
You convert natural language into robot navigation commands.

Valid destinations are:

red
green
blue
yellow
origin

Understand natural language, including:

- Short forms and first letters:
  - r -> red
  - g -> green
  - b -> blue
  - y -> yellow
  - o -> origin

- Minor spelling mistakes and typos, for example:
  - gren, grean -> green
  - blu, blew -> blue
  - yelow, yellow -> yellow
  - reed, rd -> red
  - orgin, originn -> origin

Examples:

go to green
take me to green
drive to blue
head over to yellow
go home
return to origin
come back
go back where you started
go back to the previous place
return there
go there
go where we were before
go to g
take me to b
go r
go y
return to o

If the user refers to

- where you started
- starting point
- beginning
- home

return

origin

If they refer to

- previous place
- last place
- go back there
- previous destination

return the previous destination supplied in memory.

If multiple destinations are requested

"go to blue then green then red"

return

blue,green,red

Respond ONLY with

red
green
blue
yellow
origin

or a comma separated sequence.

Do not explain your answer.
Do not include any extra text.
"""

class LotInputBot1(Node):
    def __init__(self):
        super().__init__('lot_input_bot1', namespace=BOT_NAMESPACE)
        self.pub = self.create_publisher(String, 'target_lot', 10)
        self.create_subscription(String, 'lot_status', self.status_cb, 10)

        self.api_key = "your_key"
        if not self.api_key:
            self.get_logger().error(
                "GROQ_API_KEY is not set in the environment. "
                "Run: export GROQ_API_KEY=\"your-key-here\" and restart."
            )
            raise RuntimeError("GROQ_API_KEY not set")

        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

        # full-session conversation memory: list of {"role", "content"}
        # dicts, grows for the lifetime of this node, included on every
        # Groq request so it can resolve context-dependent phrasing.
        self._history = []

        # semantic action filtering state: tracks the bot's last
        # accepted target and whether it's currently stopped, so
        # redundant/no-op commands can be caught before publish.
        self._last_target = None
        self._is_stopped = True

        self.get_logger().info(
            f"[{BOT_NAMESPACE}] Type a command in natural language "
            "(e.g. 'go to the green lot', or 'stop'), Enter to send, "
            "'quit' to exit."
        )

    def status_cb(self, msg):
        data = msg.data
        if data.startswith("reached:"):
            print(f"\n[{BOT_NAMESPACE}] Confirmed: reached {data.split(':', 1)[1]}.\n")
        elif data.startswith("heading_to:"):
            print(f"\n[{BOT_NAMESPACE}] Heading to {data.split(':', 1)[1]}.\n")
        elif data.startswith("unknown_lot:"):
            print(f"\n[{BOT_NAMESPACE}] Rejected unknown target: '{data.split(':', 1)[1]}'\n")
        elif data.startswith("failed:"):
            print(f"\n[{BOT_NAMESPACE}] Nav2 failed to reach {data.split(':', 1)[1]}.\n")
        elif data.startswith("waiting_for_lot:"):
            print(f"\n[{BOT_NAMESPACE}] Lot occupied, queued for {data.split(':', 1)[1]}.\n")
        elif data.startswith("waiting:"):
            print(f"\n[{BOT_NAMESPACE}] Pausing {data.split(':', 1)[1]}s before next lot in sequence.\n")
        elif data.startswith("canceled:"):
            print(f"\n[{BOT_NAMESPACE}] Canceled en route to {data.split(':', 1)[1]} (new command received).\n")
        elif data.startswith("stopped:"):
            print(f"\n[{BOT_NAMESPACE}] Stopped. Holding position until next command.\n")

    def _parse_command(self, text):
        """
        Send text + full session history to Groq. Returns:
          - a valid lot color string, e.g. "green"
          - a comma-separated sequence, e.g. "blue,green"
          - the literal string "stop"
          - None if nothing resolved
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self._history)
        messages.append({"role": "user", "content": text})

        payload = {
            "model": GROQ_MODEL,
            "temperature": 0,
            "max_tokens": 20,
            "messages": messages,
        }
        try:
            resp = self._session.post(GROQ_URL, data=json.dumps(payload), timeout=5)
            resp.raise_for_status()
        except requests.RequestException as e:
            self.get_logger().warn(f"Groq request failed: {e}")
            return None

        try:
            content = resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            self.get_logger().warn(f"Unexpected Groq response shape: {e}")
            return None

        reply = content.strip().lower().strip(".!'\" ")

        # record this exchange in memory regardless of outcome, so future
        # turns can reference it (including failed/unclear ones).
        self._history.append({"role": "user", "content": text})
        self._history.append({"role": "assistant", "content": reply})

        if reply == STOP_WORD:
            return STOP_WORD
        if reply in VALID_LOTS:
            return reply
        # comma-separated multi-leg sequence — validate every leg
        legs = reply.split(",")
        if legs and all(leg in VALID_LOTS for leg in legs):
            return reply
        return None

    def _semantic_filter(self, result):
        """
        Semantic Action Filtering: sanity-checks a parsed result against
        the bot's current state before it's allowed through to publish.

        - Collapses consecutive duplicate legs in a sequence, e.g.
          "red,red,green" -> "red,green".
        - Drops a single-target command that just repeats the target
          the bot is already at/heading to.

        Returns the (possibly modified) result, or None if the action
        should be filtered out entirely.
        """
        legs = result.split(",")
        deduped = [legs[0]]
        for leg in legs[1:]:
            if leg != deduped[-1]:
                deduped.append(leg)
        filtered = ",".join(deduped)

        if (len(deduped) == 1 and deduped[0] == self._last_target
                and not self._is_stopped):
            print(
                f"[{BOT_NAMESPACE}] Already heading to/at '{deduped[0]}', "
                "ignoring repeat command."
            )
            return None

        return filtered

    def run(self):
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.0)
            try:
                cmd = input(f"[{BOT_NAMESPACE}] Enter command: ").strip()
            except EOFError:
                break
            if not cmd:
                continue
            if cmd.lower() == 'quit':
                break

            result = self._parse_command(cmd)
            if result is not None:
                result = self._semantic_filter(result)

            if result == STOP_WORD:
                self.pub.publish(String(data=STOP_WORD))
                self.get_logger().info(f"[{BOT_NAMESPACE}] Stop requested.")
                self._is_stopped = True
            elif result is not None:
                self.pub.publish(String(data=result))
                self.get_logger().info(f"[{BOT_NAMESPACE}] Target set: {result}")
                self._last_target = result.split(",")[-1]
                self._is_stopped = False
            else:
                print(
                    "Couldn't figure out a lot from that. "
                    "Try mentioning red, green, blue, yellow, origin, or 'stop'."
                )

    def destroy_node(self):
        self._session.close()
        super().destroy_node()


def main():
    rclpy.init()
    try:
        node = LotInputBot1()
    except RuntimeError:
        rclpy.shutdown()
        return
    node.run()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
