---
title:  Supported host configurations
pagenum: 1
---

The table below lists the host operating systems can be used to build and run the container images produced by ue4-docker, as well as which features are supported under each system. **Click on an operating system's name to view the configuration instructions for that platform.**

{::nomarkdown}
<table class="host-systems">
	<thead>
		<tr>
			<th>Host OS</th>
			<th>Linux containers</th>
			<th>Windows containers</th>
			<th>NVIDIA Container Toolkit</th>
			<th>Optimality</th>
		</tr>
	</thead>
	<tbody>
		{% for host in site.data.ue4-docker.hosts %}
			<tr>
				<td><a href="{{ host.link | uri_escape }}"><strong>{{ host.name | escape }}</strong></a></td>
				<td class="{% if host.linux == "Yes" %}supported{% else %}unsupported{% endif %}">{{ host.linux | escape }}</td>
				<td class="{% if host.windows == "Yes" %}supported{% else %}unsupported{% endif %}">{{ host.windows | escape }}</td>
				<td class="{% if host.gpu == "Yes" %}supported{% else %}unsupported{% endif %}">{{ host.gpu | escape }}</td>
				<td class="{% if host.optimality contains "Optimal" %}supported{% else %}unsupported{% endif %}">{{ host.optimality | escape }}</td>
			</tr>
		{% endfor %}
	</tbody>
</table>
{:/}

The ***Optimality*** column indicates whether a given host operating system provides the best experience for running the container types that it supports. The configuration instructions page for each operating system provides further details regarding the factors that make it either optimal or sub-optimal.
