#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk
pygtk.require('2.0')
import gtk
import os, time, gobject,platform

def notify(nome, testo):
	if platform.system()=='Windows':
		os.system('notifu /t warn /d 8000 /m "Timer:  %s  %s"'%(nome,testo))
	else:
		os.system('notify-send "Timer %s" "%s" -u critical'%(nome, testo))

def label_exp_gen(text, container):
	label = gtk.Label(text) 
	container.pack_start(label, True, True, 0)
	label.show()
	return label
def label_gen(text, container):
	label = gtk.Label(text) 
	container.pack_start(label, False, False, 0)
	label.show()
	return label
def button_gen(label, callback, container):
	button = gtk.Button(label)
	button.connect("clicked", callback)
	container.pack_start(button, False, False, 5)
	button.show()
	return button
def entry_gen(callback, container):
	entry = gtk.Entry()
	entry.connect("activate", callback)
	container.pack_start(entry, False, False, 5)
	entry.show()
	return entry
def hbox_avviso_gen(vbox_avvisi, avvia_callback, aggiungi_avviso):
	hbox_avviso = gtk.HBox(False, 0)
	hbox_avviso.show()
	vbox_avvisi.pack_start(hbox_avviso, False, False, 0)
	entry_avviso = entry_gen(avvia_callback, hbox_avviso)
	entry_avviso.set_tooltip_text("in minuti")
	button_avviso = gtk.Button("+")
	button_avviso.show()
	button_avviso.set_size_request(30, -1)
	button_avviso.handler_id = button_avviso.connect("clicked", aggiungi_avviso, hbox_avviso)
	hbox_avviso.pack_start(button_avviso, False, False, 5)
	return hbox_avviso, entry_avviso
def completion_gen(completion_list, callback):
	completion = gtk.EntryCompletion()
	liststore = gtk.ListStore(str)
	for nome in completion_list:
		liststore.append([nome])
	completion.set_model(liststore)
	completion.set_text_column(0)
	completion.connect('match-selected', callback)
	return completion

class Timer:
	def __init__(self):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.connect("delete_event", self.quit_callback)
		self.window.set_title("Timer")
		self.window.set_border_width(10)
		self.window.set_resizable(False)
		self.window.show()
		
		self.T0 = 0
		self.tempo = '00:00.00'
		self.conteggio = False
		self.nome = ''
		
		if os.path.exists(os.path.join(os.getcwd(),'timer.salvages')):
			f = open(os.path.join(os.getcwd(),'timer.salvages'))
			self.salvages = eval(f.readline())
			f.close()
		else:
			self.salvages = {}
			f = open(os.path.join(os.getcwd(),'timer.salvages'), 'w')
			f.write(str(self.salvages))
			f.close()
			
		self.tutto = gtk.HBox()
		self.tutto.show()
		self.window.add(self.tutto)
		
		###	LayoutData
		# nome, tempo
		self.box_data = gtk.HBox(False, 0)
		self.box_data.show()
		self.tutto.add(self.box_data)
		
		vbox = gtk.VBox(False, 0)
		vbox.show()
		self.box_data.pack_start(vbox, False, False, 0)
		
		hbox_avvia = gtk.HBox(False, 0)
		hbox_avvia.show()
		vbox.pack_start(hbox_avvia, False, False, 0)

		button = button_gen("  avvia  ", self.avvia_callback, hbox_avvia)
		button = button_gen("  salva  ", self.salva_callback, hbox_avvia)
		self.label_warning = label_gen("", vbox)
		
		hbox_nome = gtk.HBox()
		hbox_nome.show()
		vbox.pack_start(hbox_nome, False, False, 0)

		label = label_exp_gen("nome", hbox_nome)
		self.entry_nome = entry_gen(self.avvia_callback, hbox_nome)
		completion_list = self.salvages.keys()
		self.entry_nome.set_completion(completion_gen(completion_list, self.load_callback))
		
		hbox_tempo = gtk.HBox()
		hbox_tempo.show()
		vbox.pack_start(hbox_tempo, False, False, 0)
		label = label_exp_gen("tempo", hbox_tempo)
		self.entry_tempo = entry_gen(self.avvia_callback, hbox_tempo)
		self.entry_tempo.set_tooltip_text("in minuti")
		
		separator = gtk.VSeparator()
		separator.show()
		self.box_data.pack_start(separator, False, False, 5)
		
		# avvisi prima del termine
		self.vbox_avvisi = gtk.VBox(False, 0)
		self.vbox_avvisi.show()
		self.box_data.pack_start(self.vbox_avvisi, False, False, 0)
		
		label = label_gen("avvisi prima del termine", self.vbox_avvisi)
		
		hbox_avviso, entry_avviso = hbox_avviso_gen(self.vbox_avvisi, self.avvia_callback, self.aggiungi_avviso)
		
		###	LayoutTime
		self.box_time = gtk.VBox(False, 10)
		self.tutto.add(self.box_time)
		
		hbox_stop = gtk.HBox(False, 10)
		hbox_stop.show()
		self.box_time.pack_start(hbox_stop, False, False, 10)
		
		button = button_gen("indietro", self.stop_callback, hbox_stop)
		
		self.label_nome = gtk.Label('')
		hbox_stop.pack_start(self.label_nome, True, True, 10)
		self.label_nome.show()
		self.label_nome.set_use_markup(True)
		
		self.label_tempo = label_exp_gen('<span size="50000">%s</span>'%self.tempo, self.box_time)
		self.label_tempo.set_use_markup(True)
		
		self.clock_tick = gobject.timeout_add(100, self.update)
	
	def aggiungi_avviso(self, widget, hbox_avviso_pre):
		widget.set_label(" - ")
		widget.disconnect(widget.handler_id)
		widget.connect("clicked", self.rimuovi_avviso, hbox_avviso_pre)
		hbox_avviso, entry_avviso = hbox_avviso_gen(self.vbox_avvisi, self.avvia_callback, self.aggiungi_avviso)
		entry_avviso.grab_focus()
		self.vbox_avvisi.reorder_child(hbox_avviso, 1)
	def rimuovi_avviso(self, widget, hbox_avviso):
		self.vbox_avvisi.remove(hbox_avviso)
		self.window.resize(1,1)
	
	def salva_callback(self, widget):
		nome = self.entry_nome.get_text()
		tempo = self.entry_tempo.get_text()
		try:
			if not(nome > "" and tempo > ""): raise Exception(nome, tempo)
			lista_avvisi = []
			for hbox in self.vbox_avvisi.get_children()[1:]:
				avviso = hbox.get_children()[0].get_text()
				if avviso > "": lista_avvisi.append(avviso)
			lista_dati = [tempo, lista_avvisi]
			print nome, lista_dati
			self.salvages[nome] = lista_dati
			fs_prop = os.statvfs(os.getcwd())
			free_space = fs_prop.f_bsize * fs_prop.f_bavail
			if free_space < 10+len(str(self.salvages)): raise Exception
			f = open(os.path.join(os.getcwd(),'timer.salvages'), 'w')
			f.write(str(self.salvages))
			f.close()
			self.label_warning.set_label("salvato")
			completion_list = self.salvages.keys()
			self.entry_nome.set_completion(completion_gen(completion_list, self.load_callback))
		except:
			if  tempo == '':		self.label_warning.set_label("non salvato: manca il tempo")
			elif nome == '':		self.label_warning.set_label("non salvato: manca il nome")
			elif free_space < 50:	self.label_warning.set_label("non salvato: poco spazio sul disco")
			else:					self.label_warning.set_label("non salvato")
	def load_callback(self, completion, model, iter):
		print self.salvages[model[iter][0]], 'was selected'
		lista_dati = self.salvages[ model[iter][0] ]
		self.entry_tempo.set_text(lista_dati[0])
		lista_avvisi = lista_dati[1]
		for hbox_avviso in self.vbox_avvisi.get_children()[2:]:
			self.vbox_avvisi.remove(hbox_avviso)
		
		hbox_avviso_pre = self.vbox_avvisi.get_children()[1]
		print hbox_avviso_pre.get_children()[0].set_text('')
		for avviso in lista_avvisi:
			hbox_avviso_pre.get_children()[0].set_text(avviso)
			self.aggiungi_avviso(hbox_avviso_pre.get_children()[1], hbox_avviso_pre)
			hbox_avviso_pre = self.vbox_avvisi.get_children()[1]
		self.window.resize(1,1)
		return
			  	
	def quit_callback(self, widget, event):
		gtk.main_quit()

	def avvia_callback(self, widget):
		if self.entry_tempo.get_text() > "":
			self.nome = self.entry_nome.get_text()
			self.T0 = time.time() + 60*eval(self.entry_tempo.get_text())
			self.label_nome.set_label('<span size="15000">%s</span>'%self.nome)
			self.lista_avvisi = []
			for hbox in self.vbox_avvisi.get_children()[1:]:
				avviso = hbox.get_children()[0].get_text()
				if avviso > "": self.lista_avvisi.append(int(avviso))
			
			self.window.set_resizable(True)
			self.window.resize(self.window.get_size()[0], 1)
			self.box_data.hide()
			self.box_time.show()
			self.conteggio = True
		elif self.entry_tempo.get_text() == '':
			self.label_warning.set_label("manca il tempo")
	
	def stop_callback(self, widget):
		self.label_warning.set_label("")
		self.window.unmaximize()
		self.window.set_resizable(False)
		self.box_time.hide()
		self.box_data.show()
		self.conteggio = False
	
	def update(self):
		if self.conteggio:
			t = self.T0 - time.time()
			if t >= 0:
				self.tempo = "%0.2i:%0.2i.%0.2i"%(t/3600, (t/60)%60, t%60)
#				label_tempo_size = self.window.get_size()[1]/3
				label_tempo_size = 50
				self.label_tempo.set_label('<span size="%i000">%s</span>'%(label_tempo_size,self.tempo))
				self.label_tempo.get_layout().set_width(400)
				
				for avviso in self.lista_avvisi:
					if t < 60*avviso:
						if avviso <= 1:	notify(self.nome, "Manca meno di un minuto!!")
						else:			notify(self.nome, "Mancano meno di %i minuti!"%avviso)
						self.lista_avvisi.remove(avviso)
						
			else:
				notify(self.nome, "tempo scaduto!")
				self.label_tempo.set_label('<span size="30000">%s</span>'%"TEMPO SCADUTO!")
				self.conteggio = False
		return True

timer = Timer()
gtk.main()
