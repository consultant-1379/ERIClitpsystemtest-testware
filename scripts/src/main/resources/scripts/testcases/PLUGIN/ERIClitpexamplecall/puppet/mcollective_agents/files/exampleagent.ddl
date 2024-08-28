metadata :name        => "exampleagent",
         :description => "Example agent that serves as an example",
         :author      => "Julio Iglesias",
         :license     => "Ericcson",
         :version     => "1.0",
         :url         => "http://badgerbadgerbadger.com",
         :timeout     => 10

action "serve_as_example", :description => "Be an illustration how to create an agent" do

    display :always

    input :echo_string,
          :prompt      => "String to echo",
          :description => "String to echo",
          :type        => :string,
          :validation  => '^.+$',
          :optional    => false,
          :maxlength   => 300

    output :status,
           :description => "The output of the command",
           :display_as  => "Command result",
           :default     => "no output"
    summarize do
      aggregate summary(:status)
    end
end
