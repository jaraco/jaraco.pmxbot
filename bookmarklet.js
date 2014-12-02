javascript:(
    function(){
        if(!window.pmxbot){
            function closeModal(){
                document.body.style.overflow = "initial";
                o.style.display = "none";
                window.pmxbot = false;
                enable_scroll();
            }
            function keydown(e) {
                if(e.which>32&&e.which<41) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                }
            }
            function wheel(e) {
                 e.preventDefault;
            }
            function disable_scroll() {
                 window.addEventListener("DOMMouseScroll", wheel);
                 window.addEventListener("keydown", keydown);
            }
            function enable_scroll() {
                window.removeEventListener("DOMMouseScroll", wheel);
                window.removeEventListener("keydown", keydown);
            }
            window.pmxbot = true;
            disable_scroll();
            var base_url = "";
            var d=document.createElement("div"),
            o = document.createElement("div");
            o.setAttribute("style","position:absolute;width:100%;background-color:rgba(0,0,0,.5);z-index:2147483647;text-align:center");
            o.id="pmxover";
            o.style.height = window.innerHeight+"px";
            o.style.top = window.scrollY+"px";
            o.style.left = window.scrollX+"px";
            var st = "padding:1em;background:#fff;border:1px #ccc solid;margin:.5em;width:90%;border-radius:0;",
                t="font-family:Helvetica,Arial";
            d.setAttribute("style","background-color:#eee;padding: 1em;text-align:center;width:25em;position:relative;top:50%;transform:translateY(-50%);margin:auto;box-shadow:0 0 30px #555;border-radius:0.25em;"+t);
            document.body.appendChild(o);
            o.appendChild(d);
            document.body.style.overflow = "hidden";
            var f=document.createElement("form"),
                s=document.createElement("input"),
                c=document.createElement("input");
            s.setAttribute("type","submit");
            c.setAttribute("type","button");
            f.innerHTML = "<span style='font-size:2em;float:left;padding-left:.2em;color:#666'>pmxbot</span><input id='pmxmsg' placeholder='Message' style='"+st+t+"' autofocus><br><input id='pmxchn' placeholder='Channel' style='"+st+t+"'>";
            var n= "margin:.5em;width:42.5%;cursor:pointer;padding:.5em;";
            s.setAttribute("style","background:#5dc251;border:0;box-shadow:0 3px 0 #409936;color:#dbf0df;"+n+t);
            c.setAttribute("style","background:#f66;border:0;box-shadow:0 3px 0 #e01414;color:#fcc;"+n+t);
            s.setAttribute("value", "Submit");
            c.setAttribute("value", "Cancel");
            f.setAttribute("style", "margin-bottom:0");
            f.appendChild(s);
            f.appendChild(c);
            d.appendChild(f);
            document.getElementById("pmxmsg").focus();
            document.getElementById("pmxchn").value=localStorage.getItem("strchn")||"";
            document.getElementById("pmxchn").addEventListener("change", function(){
                if (this.value)
                    localStorage.setItem("strchn", this.value);
            });
            f.addEventListener("submit", function(e){
                e.stopImmediatePropagation();
                e.preventDefault();
                alert("Submitting"); //TMP
                var xmlhttp = new XMLHttpRequest();
                xmlhttp.setRequestHeader("Content-type","text/plain");
                xmlhttp.open("POST", base_url + document.getElementById("pmxchn").value, true);
                xmlhttp.send(document.getElementById("pmxmsg").value);
                xmlhttp.onload = function() {
                    if(xmlhttp.status===200) {
                        alert("Success!");
                        closeModal();
                    }
                    else alert("Err: Received Code: "+xmlhttp.status);
                };
                xmlhttp.onerror = function() {
                    alert("POST Failed");
                };
            });
            o.addEventListener("click", function(e){
                e.stopImmediatePropagation();
                if(e.target.id==="pmxover")
                    closeModal();
            });
            o.addEventListener("keyup", function(e){
                if(e.which===27)
                    closeModal();
            });
            c.addEventListener("click", function(e){
                e.stopImmediatePropagation();
                closeModal();
            });
        }
    }
)();
