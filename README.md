# portshell

I'm exploring the feasability of a portage-related tool that could be useful.
It would consist of a TUI that allows you to tweak your USE flags and keywords
while letting you know immediately of the effect of the changes on dependencies.

One use case I have in mind is the exploration of dependencies prior to
installing (or not) a new package. You launch `portshell <mypackage>`, look
around, play with USE flags and keywords. If you're happy with what you see,
you exit and tell the app to save your changed flags. Then you're ready to
run `emerge <mypackage>`.

One nice feature it will have is background processing. It would display
placholders for deep dependencies information and run computation while you
browse your things and update the screen when ready.

Now, let's see how far I can go...
