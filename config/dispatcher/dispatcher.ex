defmodule Dispatcher do
  use Plug.Router

  def start(_argv) do
    port = 80
    IO.puts "Starting Plug with Cowboy on port #{port}"
    Plug.Adapters.Cowboy.http __MODULE__, [], port: port
    :timer.sleep(:infinity)
  end

  plug Plug.Logger
  plug :match
  plug :dispatch

  #################
  # Stack Builder #
  #################

  match "/docker-composes/*path" do
    Proxy.forward conn, path, "http://resource/docker-composes/"
  end

  match "/container-items/*path" do
    Proxy.forward conn, path, "http://resource/container-items/"
  end

  match "/container-groups/*path" do
    Proxy.forward conn, path, "http://resource/container-groups/"
  end

  match "/container-relations/*path" do
    Proxy.forward conn, path, "http://resource/container-relations/"
  end

  match "/stack-builder-backend/*path" do
    Proxy.forward conn, path, "http://backend/"
  end

  ####################
  # Pipeline Builder #
  ####################

  match "/pipelines/*path" do
    Proxy.forward conn, path, "http://resource/pipelines/"
  end

  match "/steps/*path" do
    Proxy.forward conn, path, "http://resource/steps/"
  end

  match "/export/*path" do
    Proxy.forward conn, path, "http://export/"
  end

  ############
  # Swarm UI #
  ############

  match "/pipeline-instances/*path" do
    Proxy.forward conn, path, "http://resource/pipeline-instances/"
  end

  match "/services/*path" do
    Proxy.forward conn, path, "http://resource/services/"
  end

  match "/stacks/*path" do
    Proxy.forward conn, path, "http://resource/stacks/"
  end

  match "/statuses/*path" do
    Proxy.forward conn, path, "http://resource/statuses/"
  end

  match "/swarm/*path" do
    Proxy.forward conn, path, "http://swarm/"
  end

  match "/drchandler/*path" do
    Proxy.forward conn, path, "http://drc-handler/"
  end

  match _ do
    send_resp( conn, 404, "Route not found.  See config/dispatcher.ex" )
  end

end
