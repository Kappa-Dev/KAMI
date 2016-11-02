d3.contextMenu = function (menu, openCallback) {
	// create the div element that will hold the context menu
	d3.selectAll('.d3-context-menu').data([1])
		.enter()
		.append('div')
		.attr('class', 'd3-context-menu');
	// close menu
	d3.select('body').on('click.d3-context-menu', function() {
		d3.select('.d3-context-menu').style('display', 'none');
	});

	// this gets executed when a contextmenu event occurs
	return function(data, index) {
		if(!menu || menu.length==0) {
			d3.event.preventDefault();
			d3.event.stopPropagation();
			console.log("no context menu ^^'");
			return;
		}
		var elm = this;
		d3.selectAll('.d3-context-menu').html('');
		var list = d3.selectAll('.d3-context-menu').append('ul');
		list.selectAll('li').data(menu).enter()
			.append('li')
			.html(function(d) {
				return d.title;
			})
			.on('click', function(d, i) {
				if(typeof(d.action)!='undefined'){
					d.action(elm, data, index);
					d3.select('.d3-context-menu').style('display', 'none');
				}
			})
			.on('mouseenter',function(d,i){
				if(typeof(d.child)!='undefined' && d.child.length>0){
					d3.select(this).append('ul').selectAll('li').data(d.child).enter()
						.append('li')
						.html(function(d){ return d.title;})
						.on('click',function(d,i){
							d.action(elm,data,index);
							d3.select('.d3-context-menu').style('display', 'none');
						})
				}
			})
			.on('mouseleave',function(d,i){
				(list).selectAll('li').selectAll('ul').style('display', 'none');
			})

		// the openCallback allows an action to fire before the menu is displayed
		// an example usage would be closing a tooltip
		if (openCallback) openCallback(data, index);

		// display context menu
		d3.select('.d3-context-menu')
			.style('left', (d3.event.pageX - 2) + 'px')
			.style('top', (d3.event.pageY - 2) + 'px')
			.style('display', 'block');

		d3.event.preventDefault();
		d3.event.stopPropagation();
	};
};