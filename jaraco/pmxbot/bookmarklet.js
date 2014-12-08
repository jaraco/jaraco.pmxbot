(
    function() {
        if (!window.pmxbot) {
            function closeModal() {
                document.body.style.overflow = "initial";
                o.parentNode.removeChild(o);
                window.pmxbot = false;
                enable_scroll();
            }
            function keydown(e) {
                if (e.which > 31 && e.which < 41 && e.target === document.body) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                }
            }
            function wheel(e) {
                e.preventDefault();
                e.stopImmediatePropagation();
            }
            function disable_scroll() {
                window.addEventListener("DOMMouseScroll", wheel);
                window.addEventListener("keydown", keydown);
            }
            function enable_scroll() {
                window.removeEventListener("DOMMouseScroll", wheel);
                window.removeEventListener("keydown", keydown);
            }
            var base_url = "//ircbot.example.com/";
            window.pmxbot = true;
            disable_scroll();
            var d = document.createElement("div"),
                o = document.createElement("div");
            o.setAttribute("style", "position:absolute;width:100%;background-color:rgba(0,0,0,.5);z-index:2147483647;text-align:center");
            o.id = "pmxover";
            o.style.height = window.innerHeight + "px";
            o.style.top = window.scrollY + "px";
            o.style.left = window.scrollX + "px";
            var st = "padding:1em;background:#fff;border:1px #ccc solid;margin:.5em;width:90%;border-radius:0;",
                t = "text-align:center;font-family:Helvetica,Arial;";
            d.setAttribute("style", t + "background-color:#eee;padding: 1em;width:25em;position:relative;top:50%;transform:translateY(-50%);margin:auto;box-shadow:0 0 30px #555;border-radius:0.25em;");
            o.appendChild(d);
            document.body.appendChild(o);
            document.body.style.overflow = "hidden";
            var f = document.createElement("form"),
                s = document.createElement("input"),
                c = document.createElement("input");
            s.setAttribute("type", "submit");
            c.setAttribute("type", "button");
            f.innerHTML = "<span style='font-size:2em;float:left;padding-left:.2em;color:#666;'>pmxbot</span><input id='pmxchn' placeholder='Channel' style='" + t + st + "'><br><input id='pmxmsg' placeholder='Message' style='" + t + st + "' value='"+document.URL+"'>";
            var q = "all:initial;margin:.5em;width:42.5%;cursor:pointer;padding:.5em 0;";
            s.setAttribute("style", q + t + "background:#5dc251;border:0;box-shadow:0 3px 0 #409936;color:#dbf0df");
            c.setAttribute("style", q + t + "background:#f66;border:0;box-shadow:0 3px 0 #e01414;color:#fcc");
            s.setAttribute("value", "Submit");
            c.setAttribute("value", "Cancel");
            f.style.marginBottom = "0";
            f.appendChild(s);
            f.appendChild(c);
            d.appendChild(f);
            document.getElementById("pmxmsg").focus();
            document.getElementById("pmxchn").value = localStorage.getItem("strchn") || "";
            document.getElementById("pmxchn").addEventListener("keyup", function() {
                localStorage.setItem("strchn", this.value);
            });
            f.addEventListener("submit", function(e) {
                e.stopImmediatePropagation();
                e.preventDefault();
                var xmlhttp = new XMLHttpRequest(),
                    channel = document.getElementById("pmxchn").value,
                    data = document.getElementById("pmxmsg").value;
                xmlhttp.open("POST", base_url + channel, true);
                xmlhttp.setRequestHeader("Content-type", "text/plain");
                xmlhttp.onreadystatechange = function() {
                    if (xmlhttp.readyState === 4) {
                        if (xmlhttp.status === 200) {
                            closeModal();
                        } else alert("Err: Received Code: " + xmlhttp.status);
                    }
                };
                xmlhttp.send(data);
            });
            o.addEventListener("click", function(e) {
                e.stopImmediatePropagation();
                if (e.target.id === "pmxover")
                    closeModal();
            });
            o.addEventListener("keyup", function(e) {
                if (e.which === 27)
                    closeModal();
            });
            c.addEventListener("click", function(e) {
                e.stopImmediatePropagation();
                closeModal();
            });
        }
    }
)();
